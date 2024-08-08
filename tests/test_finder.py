""" Tests for the file finder module """

# Imports
from napari_mito_hcs import finder

from . import helpers

# Tests


class TestFileFinder(helpers.FileSystemTestCase):

    def test_finds_zero_groups(self):

        pipeline = finder.FileFinder(
            cell_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch1',
            nuclei_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch2',
            mitochondria_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch3',
        )
        indir = self.tempdir
        outdir = indir / 'out'

        res = list(pipeline(indir=indir, outdir=outdir))
        assert res == []

    def test_finds_one_group(self):

        pipeline = finder.FileFinder(
            cell_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch1',
            nuclei_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch2',
            mitochondria_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch3',
        )
        indir = self.tempdir
        outdir = indir / 'out'

        f1 = indir / 'r02c04f03ch1.tif'
        f2 = indir / 'r02c04f03ch2.tif'
        f3 = indir / 'r02c04f03ch3.tif'

        f1.touch()
        f2.touch()
        f3.touch()

        res = list(pipeline(indir=indir, outdir=outdir))
        exp = [
            finder.FileGroup(nuclei_image=f2, cell_image=f1, mitochondria_image=f3, prefix='r02c04f03', outdir=outdir),
        ]

        assert res == exp

    def test_finds_two_groups(self):

        pipeline = finder.FileFinder(
            cell_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch1',
            nuclei_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch2',
            mitochondria_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch3',
        )
        indir = self.tempdir
        outdir = indir / 'out'

        f1 = indir / 'r02c04f03ch1.tif'
        f2 = indir / 'r02c04f03ch2.tif'
        f3 = indir / 'r02c04f03ch3.tif'

        f4 = indir / 'r02c04f09ch1.tif'
        f5 = indir / 'r02c04f09ch2.tif'
        f6 = indir / 'r02c04f09ch3.tif'

        f1.touch()
        f2.touch()
        f3.touch()

        f4.touch()
        f5.touch()
        f6.touch()

        res = list(pipeline(indir=indir, outdir=outdir))
        exp = [
            finder.FileGroup(nuclei_image=f2, cell_image=f1, mitochondria_image=f3, prefix='r02c04f03', outdir=outdir),
            finder.FileGroup(nuclei_image=f5, cell_image=f4, mitochondria_image=f6, prefix='r02c04f09', outdir=outdir),
        ]

        assert res == exp

    def test_finds_two_groups_alternate_suffix(self):

        pipeline = finder.FileFinder(
            cell_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch1',
            nuclei_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch2',
            mitochondria_pattern='(r[0-9]+c[0-9]+f[0-9]+)ch3',
        )
        indir = self.tempdir
        outdir = indir / 'out'

        f1 = indir / 'r02c04f03ch1.tiff'
        f2 = indir / 'r02c04f03ch2.tiff'
        f3 = indir / 'r02c04f03ch3.tiff'

        f4 = indir / 'r02c04f09ch1.tiff'
        f5 = indir / 'r02c04f09ch2.tiff'
        f6 = indir / 'r02c04f09ch3.tiff'

        f1.touch()
        f2.touch()
        f3.touch()

        f4.touch()
        f5.touch()
        f6.touch()

        res = list(pipeline(indir=indir, outdir=outdir))
        exp = [
            finder.FileGroup(nuclei_image=f2, cell_image=f1, mitochondria_image=f3, prefix='r02c04f03', outdir=outdir),
            finder.FileGroup(nuclei_image=f5, cell_image=f4, mitochondria_image=f6, prefix='r02c04f09', outdir=outdir),
        ]

        assert res == exp
