##
# Copyright 2009-2020 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/easybuilders/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
##
"""
EasyBuild support for building and installing MrBayes, implemented as an easyblock

@author: Stijn De Weirdt (Ghent University)
@author: Dries Verdegem (Ghent University)
@author: Kenneth Hoste (Ghent University)
@author: Pieter De Baets (Ghent University)
@author: Jens Timmerman (Ghent University)
@author: Andy Georges (Ghent University)
@author: Maxime Boissonneault (Compute Canada, Calcul Quebec, Universite Laval)
"""

import os
from distutils.version import LooseVersion

from easybuild.easyblocks.generic.configuremake import ConfigureMake
from easybuild.tools.build_log import EasyBuildError
from easybuild.tools.filetools import copy_file, mkdir
from easybuild.tools.modules import get_software_root
from easybuild.tools.run import run_cmd


class EB_MrBayes(ConfigureMake):
    """Support for building/installing MrBayes."""

    def configure_step(self):
        """Configure build: <single-line description how this deviates from standard configure>"""

        # set generic make options
        self.cfg.update('buildopts', 'CC="%s" OPTFLAGS="%s"' % (os.getenv('MPICC'), os.getenv('CFLAGS')))

        if LooseVersion(self.version) >= LooseVersion("3.2") and LooseVersion(self.version) < LooseVersion("3.2.7"):
            # set correct start_dir dir, and change into it
            # test whether it already contains 'src', since a reprod easyconfig would
            if os.path.basename(self.cfg['start_dir']) != 'src':
                self.cfg['start_dir'] = os.path.join(self.cfg['start_dir'], 'src')
            try:
                os.chdir(self.cfg['start_dir'])
            except OSError as err:
                raise EasyBuildError("Failed to change to correct source dir %s: %s", self.cfg['start_dir'], err)

            # run autoconf to generate configure script
            cmd = "autoconf"
            run_cmd(cmd)

        if LooseVersion(self.version) >= LooseVersion("3.2"):
            # set config opts
            beagle = get_software_root('beagle-lib')
            if beagle:
                self.cfg.update('configopts', '--with-beagle=%s' % beagle)
            else:
                if get_software_root('BEAGLE'):
                    self.log.nosupport('BEAGLE module as dependency, should be beagle-lib', '2.0')
                raise EasyBuildError("beagle-lib module not loaded?")

            if self.toolchain.options.get('usempi', None):
                if LooseVersion(self.version) < LooseVersion("3.2.7"):
                    self.cfg.update('configopts', '--enable-mpi')
                else:
                    self.cfg.update('configopts', '--with-mpi')

            # configure
            super(EB_MrBayes, self).configure_step()
        else:

            # no configure script prior to v3.2
            self.cfg.update('buildopts', 'MPI=yes')

    def install_step(self):
        """Install by copying bniaries to install dir."""

        if LooseVersion(self.version) >= LooseVersion("3.2.7"):
            super(EB_MrBayes, self).install_step()

        else:
            bindir = os.path.join(self.installdir, 'bin')
            mkdir(bindir)

            src = os.path.join(self.cfg['start_dir'], 'mb')
            dst = os.path.join(bindir, 'mb')
            copy_file(src, dst)
            self.log.info("Successfully copied %s to %s", src, dst)

    def sanity_check_step(self):
        """Custom sanity check for MrBayes."""

        custom_paths = {
            'files': ["bin/mb"],
            'dirs': [],
        }

        super(EB_MrBayes, self).sanity_check_step(custom_paths=custom_paths)
