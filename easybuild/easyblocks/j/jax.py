"""
EasyBuild support for building and installing JAX, implemented as an easyblock

@author: Andrew Edmondson (University of Birmingham)
"""
from easybuild.framework.easyblock import EasyBlock
from easybuild.tools.systemtools import POWER, get_cpu_architecture
from easybuild.tools.modules import get_software_root, get_software_version
from easybuild.tools.run import run_cmd


class EB_JAX(EasyBlock):
    """Support for building/installing JAX."""

    def configure_step(self):
        """No configuration for JAX."""
        pass

    def build_step(self):
        """Build JAX"""
        cuda = get_software_root('CUDA')
        cudnn = get_software_root('CuDNN')
        bazel = get_software_root('Bazel')
        binutils = get_software_root('binutils')
        if not self.cfg['prebuildopts']:
            self.cfg['prebuildopts'] = 'export TF_CUDA_PATHS="{}" '.format(cuda)
            self.cfg['prebuildopts'] += 'GCC_HOST_COMPILER_PREFIX="{}/bin" '.format(binutils)
            # To prevent bazel builds on different hosts/architectures conflicting with each other
            # we'll set HOME, inside which Bazel puts active files (in ~/.cache/bazel/...)
            self.cfg['prebuildopts'] += 'HOME="{}/fake_home" && '.format(self.builddir)

        if not self.cfg['buildopts']:
            self.cfg['buildopts'] = '--enable_cuda --cuda_path "{}" '.format(cuda)
            self.cfg['buildopts'] += '--cudnn_path "{}" '.format(cudnn)
            self.cfg['buildopts'] += '--bazel_path "{}/bin/bazel" '.format(bazel)
            # Tell Bazel to pass PYTHONPATH through to what it's building, so it can find scipy etc.
            self.cfg['buildopts'] += '--bazel_options=--action_env=PYTHONPATH '
            self.cfg['buildopts'] += '--noenable_mkl_dnn '
            if get_cpu_architecture() == POWER:
                # Tell Bazel to tell NVCC to tell the compiler to use -mno-float128
                self.cfg['buildopts'] += (r'--bazel_options=--per_file_copt=.*cu\.cc.*'
                                          '@-nvcc_options=compiler-options=-mno-float128 ')

        cmd = ' '.join([
            self.cfg['prebuildopts'],
            'python build/build.py',
            self.cfg['buildopts'],
        ])

        (out, _) = run_cmd(cmd, log_all=True, simple=False)

        return out

    def install_step(self):
        """Install JAX"""
        if self.cfg['install_cmd'] is None:
            self.cfg['install_cmd'] = '(cd build && pip install --prefix {} .) &&'.format(self.installdir)
            self.cfg['install_cmd'] = 'pip install --prefix {} .'.format(self.installdir)

        super(EB_JAX, self).install_step()

    def make_module_step(self, fake=False):
        """Make the module"""

        if 'XLA_FLAGS' not in self.cfg['modextravars']:
            cuda = get_software_root('CUDA')
            self.cfg['modextravars']['XLA_FLAGS'] = "--xla_gpu_cuda_data_dir={}/bin".format(cuda)

        if 'PYTHONPATH' not in self.cfg['modextrapaths']:
            pyshortver = '.'.join(get_software_version('Python').split('.')[:2])
            self.cfg['modextrapaths']['PYTHONPATH'] = 'lib/python{}/site-packages'.format(pyshortver)

        return super(EB_JAX, self).make_module_step(fake)

    def sanity_check_step(self):
        """Custom sanity check for JAX."""
        pyshortver = '.'.join(get_software_version('Python').split('.')[:2])
        custom_paths = {
            'files': [],
            'dirs': ['lib/python{}/site-packages/jax'.format(pyshortver),
                     'lib/python{}/site-packages/jaxlib'.format(pyshortver)],
        }
        super(EB_JAX, self).sanity_check_step(custom_paths=custom_paths)
