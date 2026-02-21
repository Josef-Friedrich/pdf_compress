import argparse
import os
import shutil
import subprocess
import tempfile
import time
from os.path import exists
from pathlib import Path
from subprocess import check_output, run
from unittest import mock
from unittest.mock import Mock, patch

import pytest
from _helper import check_internet_connectifity, download

import pdf_compress
from pdf_compress import FilePath, State, Timer, check_dependencies, list_files


def get_state():
    args = Mock()
    args.threshold = "50%"
    args.input_files = ["/tmp/1.txt", "/tmp/2.txt"]
    state = State(args)
    return state


def copy(path: str):
    basename: str = os.path.basename(path)
    tmp: str = os.path.join(tempfile.mkdtemp(), basename)
    return shutil.copy(path, tmp)


def output_pdfinfo(pages: int = 3):
    return "".join(
        [
            "Creator:        c42pdf v. 0.12 args:  -p 658.80x866.52\n",
            "Producer:       PDFlib V0.6 (C) Thomas Merz 1997-98\n",
            "CreationDate:   Sat Jan  2 21:11:06 2010 CET\n",
            "Tagged:         no\n",
            "UserProperties: no\nSuspects:       no\n",
            "Form:           none\n",
            "JavaScript:     no\n",
            "Pages:          {}\n".format(pages),
            "Encrypted:      no\n",
            "Page size:      658.8 x 866.52 pts\n",
            "Page rot:       0\n",
            "File size:      343027 bytes\n",
            "Optimized:      no\n",
            "PDF version:    1.1\n",
        ]
    )


def convert_to_cli_list(run_args_list):
    output = []
    for args in run_args_list:
        output.append(" ".join(args[0][0]))
    return output


def patch_mulitple(args, pdf_page_count=5):
    with (
        patch("sys.argv", ["cmd"] + list(args)),
        patch("pdf_compress.check_dependencies"),
        patch("pdf_compress.run.run") as run_run,
        patch("pdf_compress.run.check_output") as run_check_output,
        patch("pdf_compress.do_pdfinfo_page_count") as do_pdfinfo_page_count,
        patch("os.path.getsize") as os_path_getsize,
        patch("os.listdir") as os_listdir,
        patch("os.remove") as os_remove,
    ):
        tiff1 = "1_{}.tiff".format(pdf_compress.tmp_identifier)
        tiff2 = "2_{}.tiff".format(pdf_compress.tmp_identifier)
        files = [tiff2, tiff1, "3.tif"]
        os_listdir.return_value = files
        os_path_getsize.return_value = 300
        run_run.return_value.returncode = 0
        do_pdfinfo_page_count.return_value = 5
        pdf_compress.main()
    return {
        "run_run": run_run,
        "run_run_cli_list": convert_to_cli_list(run_run.call_args_list),
        "run_check_output": run_check_output,
        "os_path_getsize": os_path_getsize,
        "os_listdir": os_listdir,
        "os_remove": os_remove,
        "state": pdf_compress.state,
    }


dependencies = check_dependencies(*pdf_compress.dependencies, raise_error=False)
internet = check_internet_connectifity()

if dependencies and internet:
    tmp_pdf = download("pdf/scans.pdf", local_path="/tmp/jfs-pdf_compress/test.pdf")
    tmp_png1 = download(
        "png/bach-busoni_300.png",
        local_path="/tmp/jfscripts/pdf_compress/bach-busoni_300.png",
    )
    tmp_png2 = download(
        "png/liszt-weinen_300.png",
        local_path="/tmp/jfscripts/pdf_compress/liszt-weinen_300.png",
    )
    tmp_tiff1 = download(
        "tiff/bach-busoni_300.tiff",
        local_path="/tmp/jfscripts/pdf_compress/bach-busoni_300.tiff",
    )
    tmp_tiff2 = download(
        "tiff/liszt-weinen_300.tiff",
        local_path="/tmp/jfscripts/pdf_compress/liszt-weinen_300.tiff",
    )
    tmp_ocr = download(
        "ocr/Walter-Benjamin_Einbahnstrasse.jpg",
        local_path="/tmp/jfscripts/pdf_compress/ocr.jpg",
    )


class TestUnit:
    @mock.patch("pdf_compress.run.check_output")
    def test_get_pdf_info(self, check_output):
        check_output.return_value = output_pdfinfo(5)
        result = pdf_compress.do_pdfinfo_page_count("test.pdf")
        assert result == 5

    @mock.patch("pdf_compress.run.check_output")
    def test_do_magick_identify(self, check_output):
        check_output.side_effect = [
            bytes("2552".encode("utf-8")),
            bytes("3656".encode("utf-8")),
            bytes("256".encode("utf-8")),
        ]
        result = pdf_compress.do_magick_identify(FilePath("test.pdf"))
        assert result == {"width": 2552, "height": 3656, "colors": 256}

    def test_enlighten_border(self):
        result = pdf_compress._do_magick_convert_enlighten_border(1000, 1000)
        assert result == [
            "-region",
            "950x50",
            "-level",
            "0%,30%",
            "-region",
            "50x950+950",
            "-level",
            "0%,30%",
            "-region",
            "950x50+50+950",
            "-level",
            "0%,30%",
            "-region",
            "50x950+0+50",
            "-level",
            "0%,30%",
        ]

    @patch("pdf_compress.do_magick_convert")
    def test_subcommand_samples(self, do_magick_convert):
        state = get_state()
        pdf_compress.subcommand_samples(FilePath("test.jpg"), state)
        assert do_magick_convert.call_count == 29

    def test_check_threshold(self):
        check = pdf_compress.check_threshold
        assert check(1) == "1%"
        assert check("2") == "2%"
        assert check("3%") == "3%"

        with pytest.raises(ValueError):
            check(4.5)
        with pytest.raises(ValueError):
            check("lol")
        with pytest.raises(argparse.ArgumentTypeError):
            check(-1)
        with pytest.raises(argparse.ArgumentTypeError):
            check(101)

    def test_do_pdfimages(self):
        state = get_state()
        with mock.patch("subprocess.run") as mock_run:
            pdf_compress.do_pdfimages(FilePath("test.pdf"), state)
            args = mock_run.call_args[0][0]
            assert args[0] == "pdfimages"
            assert args[1] == "-tiff"
            assert args[2] == "test.pdf"
            assert "test.pdf" in args[2]
            # test_magick_901ca3ae-c5ad-11e8-9796-5c514fcf0a5d
            assert len(args[3]) == 48
            assert args[3].startswith("test_")

    @patch("os.path.getsize")
    @patch("os.listdir")
    def test_collect_images(self, listdir, getsize):
        state = get_state()
        tiff1 = "1_{}.tif".format(pdf_compress.tmp_identifier)
        tiff2 = "2_{}.tif".format(pdf_compress.tmp_identifier)
        files = [tiff2, tiff1, "3.tif"]
        listdir.return_value = files
        getsize.return_value = 300
        output = pdf_compress.collect_images(state)
        assert output == [
            os.path.join(state.common_path, tiff1),
            os.path.join(state.common_path, tiff2),
        ]

    @patch("pdf_compress._do_magick_command")
    @patch("pdf_compress.run.run")
    def test_do_magick_convert_without_kwargs(self, run, _do_magick_command):
        _do_magick_command.return_value = ["convert"]
        pdf_compress.do_magick_convert(
            FilePath("test.tif"),
            FilePath("test.tiff"),
        )
        run.assert_called_with(
            [
                "convert",
                "-units",
                "PixelsPerInch",
                "-compress",
                "Group4",
                "-monochrome",
                "test.tif",
                "test.tiff",
            ]
        )

    @patch("pdf_compress._do_magick_command")
    @patch("pdf_compress.run.run")
    def test_do_magick_convert_kwargs(self, run, _do_magick_command):
        _do_magick_command.return_value = ["convert"]
        pdf_compress.do_magick_convert(
            FilePath("test.tif"),
            FilePath("test.pdf"),
            threshold="60%",
            enlighten_border=False,
            border=True,
            resize=True,
            trim=True,
            deskew=True,
        )
        run.assert_called_with(
            [
                "convert",
                "-units",
                "PixelsPerInch",
                "-resize",
                "200%",
                "-deskew",
                "40%",
                "-threshold",
                "60%",
                "-trim",
                "+repage",
                "-border",
                "5%",
                "-bordercolor",
                "#FFFFFF",
                "-compress",
                "Group4",
                "-monochrome",
                "test.tif",
                "test.pdf",
            ]
        )

    @patch("pdf_compress.run.run")
    def test_do_tesseract(self, run):
        pdf_compress.do_tesseract(FilePath("test.tiff"))
        assert run.call_args[0][0] == [
            "tesseract",
            "-l",
            "deu+eng",
            "test.tiff",
            "test",
            "pdf",
        ]

    @patch("pdf_compress.run.run")
    def test_do_tesseract_one_language(self, run):
        pdf_compress.do_tesseract(FilePath("test.tiff"), languages=["deu"])
        assert run.call_args[0][0] == [
            "tesseract",
            "-l",
            "deu",
            "test.tiff",
            "test",
            "pdf",
        ]


class TestUnitUnifyPageSize:
    def mock_pdf2_pages(self, *page_dimensions):
        output = []
        for dimension in page_dimensions:
            mock = Mock()
            mediaBox = Mock()
            mediaBox.getWidth.return_value = dimension[0]
            mediaBox.getHeight.return_value = dimension[1]
            mock.mediaBox = mediaBox
            output.append(mock)
        return output

    def run(self, margin, *dimensions):
        with (
            patch("PyPDF2.PdfFileReader") as reader,
            patch("PyPDF2.PdfFileWriter"),
            patch("PyPDF2.PageObject.createBlankPage") as blank,
            patch("pdf_compress.open"),
        ):
            reader.return_value.pages = self.mock_pdf2_pages(*dimensions)
            pdf_compress.unify_page_size(
                FilePath("test.pdf"), FilePath("out.pdf"), margin
            )
        return {
            "reader": reader,
            "blank": blank,
        }

    def test_single_page(self):
        result = self.run(3, (1, 2))
        blank = result["blank"]
        blank.assert_called_with(None, 7, 8)
        args = blank.return_value.mergeScaledTranslatedPage.call_args[0]
        assert args[1] == 1
        assert args[2] == 3
        assert args[3] == 3

    def test_multiple_page(self):
        result = self.run(3, (1, 2), (3, 4))
        blank = result["blank"]
        blank.assert_called_with(None, 9, 10)
        args = blank.return_value.mergeScaledTranslatedPage.call_args[0]
        assert args[1] == 1
        assert args[2] == 3
        assert args[3] == 3

    def test_margin(self):
        result = self.run(4, (1, 2))
        blank = result["blank"]
        args = blank.return_value.mergeScaledTranslatedPage.call_args[0]
        assert args[2] == 4
        assert args[3] == 4


class TestUnitOnMain:
    ###########################################################################
    # convert
    ###########################################################################

    def test_multiple_input_files(self):
        p = patch_mulitple(("convert", "one.tif", "two.tif"))
        call_args_list = p["run_run"].call_args_list
        assert len(call_args_list) == 2
        assert "one.tif" in " ".join(call_args_list[0][0][0])
        assert "two.tif" in " ".join(call_args_list[1][0][0])

    def test_global_state_object(self):
        assert pdf_compress.identifier == "magick"

    ##
    # Options
    ##

    # auto_black_white
    def test_convert_option_auto_black_white(self):
        p = patch_mulitple(("convert", "--auto-black-white", "test.pdf"))
        # 0: pdfimages
        # 1: magick convert
        # 2: tesseract
        # 3: magick convert
        # 4: tesseract
        # 5: pdftk
        cli_list = p["run_run_cli_list"]
        assert "pdfimages -tiff" in cli_list[0]

        assert "-threshold" in cli_list[1]
        assert "-compress Group4 -monochrome" in cli_list[1]
        assert ".tiff" in cli_list[1]

        assert ".tiff" in cli_list[2]

        assert "convert" in cli_list[3]
        assert "tesseract" in cli_list[4]
        assert "pdftk" in cli_list[5]

    # auto_color
    def test_convert_option_auto_color(self):
        p = patch_mulitple(("convert", "--auto-color", "test.pdf"))
        # 0: pdfimages
        # 1: magick convert
        # 2: tesseract
        # 3: magick convert
        # 4: tesseract
        # 5: pdftk
        cli_list = p["run_run_cli_list"]
        assert "pdfimages -tiff" in cli_list[0]

        assert "-threshold" not in cli_list[1]
        assert "-quality 75" in cli_list[1]
        assert ".jp2" in cli_list[1]

        assert ".jp2" in cli_list[2]

        assert "convert" in cli_list[3]
        assert "tesseract" in cli_list[4]
        assert "pdftk" in cli_list[5]

    # blur
    def test_convert_option_blur(self):
        p = patch_mulitple(("convert", "--blur", "3", "test.tiff"))
        assert "-blur 3" in p["run_run_cli_list"][0]

    # deskew
    def test_convert_option_deskew_true(self):
        p = patch_mulitple(("convert", "--deskew", "test.tiff"))
        assert "-deskew 40%" in p["run_run_cli_list"][0]

    def test_convert_option_deskew_false(self):
        p = patch_mulitple(("convert", "test.tiff"))
        assert "-deskew 40%" not in p["run_run_cli_list"][0]

    # join
    def test_input_pdf_join(self):
        p = patch_mulitple(("convert", "--join", "test.pdf"))
        assert len(p["run_run"].call_args_list) == 4

    # ocr
    def test_convert_ocr(self):
        p = patch_mulitple(("convert", "--ocr", "one.tif"))
        cmd_args = p["run_run"].call_args[0][0]
        assert cmd_args[1] != "-l"
        assert cmd_args[3] == "pdf"

    # ocr_language
    def test_convert_ocr_language(self):
        p = patch_mulitple(("convert", "--ocr", "one.tif", "--ocr-language", "xxx"))
        cmd_args = p["run_run"].call_args[0][0]
        assert cmd_args[:3] == ["tesseract", "-l", "xxx"]

    def test_convert_ocr_language_multiple(self):
        p = patch_mulitple(
            ("convert", "--ocr", "one.tif", "--ocr-language", "xxx", "yyy")
        )
        cmd_args = p["run_run"].call_args[0][0]
        assert cmd_args[:3] == ["tesseract", "-l", "xxx+yyy"]

    def test_convert_ocr_languages_mid(self):
        p = patch_mulitple(
            ("convert", "--ocr", "--ocr-language", "xxx", "zzz", "--", "one.tif")
        )
        cmd_args = p["run_run"].call_args[0][0]
        assert cmd_args[:3] == ["tesseract", "-l", "xxx+zzz"]

    # trim
    def test_convert_option_trim_true(self):
        p = patch_mulitple(("convert", "--trim", "test.tiff"))
        assert "-trim +repage" in p["run_run_cli_list"][0]

    def test_convert_option_trim_false(self):
        p = patch_mulitple(("convert", "test.tiff"))
        assert "-trim +repage" not in p["run_run_cli_list"][0]

    # quality
    def test_convert_option_quality(self):
        p = patch_mulitple(("convert", "--quality", "50", "test.tiff"))
        cli_list = p["run_run_cli_list"]
        assert "-quality 50" in cli_list[0]
        assert ".jp2" in cli_list[0]

    ###########################################################################
    # samples
    ###########################################################################

    def test_samples_no_options_jpg(self):
        p = patch_mulitple(("samples", "test.jpg"))
        cli_list = p["run_run_cli_list"]
        assert "test_threshold-40.tiff" in cli_list[0]
        assert "-threshold 40%" in cli_list[0]
        assert "test_quality-40.pdf" in cli_list[12]
        assert "-quality 40" in cli_list[12]
        assert "-blur 1" in cli_list[24]

    def test_samples_no_options_pdf(self):
        p = patch_mulitple(("samples", "test.pdf"))
        cli_list = p["run_run_cli_list"]
        assert "pdfimages -tiff" in cli_list[0]
        assert "threshold-40.tiff" in cli_list[1]
        assert "-threshold 40%" in cli_list[1]
        assert "quality-40.pdf" in cli_list[13]
        assert "-quality 40" in cli_list[13]

    # quality
    def test_samples_option_quality_jpg(self):
        p = patch_mulitple(("samples", "--quality", "test.jpg"))
        cli_list = p["run_run_cli_list"]
        assert len(cli_list) == 12
        assert "test_quality-40.pdf" in cli_list[0]
        assert "-quality 40" in cli_list[0]

    # threshold
    def test_samples_option_threshold_jpg(self):
        p = patch_mulitple(("samples", "--threshold", "test.jpg"))
        cli_list = p["run_run_cli_list"]
        assert len(cli_list) == 12
        assert "test_threshold-40.tiff" in cli_list[0]
        assert "-threshold 40%" in cli_list[0]


class TestClassTimer:
    def test_start(self):
        timer = Timer()
        assert timer.begin > 0

    def test_stop(self):
        timer = Timer()
        result = timer.stop()
        assert "s" in result


class TestClassState:
    def setup_method(self):
        self.state = get_state()

    def test_args(self):
        assert self.state.args


class TestModuleGlobals:
    def test_identifier(self):
        assert pdf_compress.identifier == "magick"

    def test_tmp_identifier(self):
        assert len(pdf_compress.tmp_identifier) == len(pdf_compress.identifier) + 36 + 1


class TestIntegration:
    @pytest.mark.skip
    def test_option_version(self):
        output = subprocess.check_output(["pdf-compress.py", "--version"])
        assert output
        assert "pdf-compress.py" in str(output)


@pytest.mark.skipif(
    not dependencies or not internet, reason="Some dependencies are not installed"
)
class TestIntegrationWithDependencies:
    ##
    # convert
    ##

    def test_input_file_pdf_exception(self):
        out = run(
            ["pdf-compress.py", "convert", "test1.pdf", "test2.pdf"],
            encoding="utf-8",
            stderr=subprocess.PIPE,
        )
        assert out.returncode == 1
        assert "Specify only one PDF file." in out.stderr

    def test_with_real_pdf(self):
        tmp = copy(tmp_pdf)
        assert exists(tmp)
        path = FilePath(tmp)
        check_output(["pdf-compress.py", "convert", tmp])
        result = ("0.tiff", "1.tiff", "2.tiff")
        for test_file in result:
            assert exists(path.base + "-00" + test_file)

    def test_with_real_pdf_join(self):
        tmp = copy(tmp_pdf)
        assert exists(tmp)
        check_output(["pdf-compress.py", "convert", "--pdf", "--join", tmp])
        assert exists(os.path.join(str(Path(tmp).parent), "test_magick.pdf"))

    def test_option_join_without_pdf(self):
        pdf = copy(tmp_pdf)
        assert exists(pdf)
        check_output(["pdf-compress.py", "convert", "--join", pdf])
        assert exists(os.path.join(str(Path(pdf).parent), "test_magick.pdf"))

    def test_option_join_pdf_source_png(self):
        assert exists(tmp_png1)
        assert exists(tmp_png2)
        check_output(
            ["pdf-compress.py", "convert", "--pdf", "--join", tmp_png1, tmp_png2]
        )
        assert exists(
            os.path.join(str(Path(tmp_png1).parent), "bach-busoni_300_magick.pdf")
        )

    def test_real_invalid_threshold(self):
        out = run(
            ["pdf-compress.py", "convert", "--threshold", "1000", "test.pdf"],
            encoding="utf-8",
            stderr=subprocess.PIPE,
        )
        assert out.returncode == 2
        assert "1000 is an invalid int value. Should be 0-100" in out.stderr

    def test_real_backup_no_backup(self):
        tmp = copy(tmp_tiff1)
        check_output(["pdf-compress.py", "convert", tmp])
        backup = FilePath(tmp).new(append="_backup", extension="tiff")
        assert not exists(str(backup))

    def test_real_backup_do_backup(self):
        tmp = copy(tmp_tiff1)
        check_output(["pdf-compress.py", "convert", "--backup", tmp])
        backup = FilePath(tmp).new(append="_backup", extension="tiff")
        assert exists(str(backup))

    def test_already_converted(self):
        tmp = copy(tmp_tiff1)
        check_output(["pdf-compress.py", "convert", tmp])
        # The test fails sometimes. Maybe we should wait a little bit.
        time.sleep(2)
        out = check_output(["pdf-compress.py", "convert", tmp])
        assert "The output file has already been converted." in out.decode("utf-8")

    def test_option_border(self):
        tiff = copy(tmp_tiff1)

        info_before = pdf_compress.do_magick_identify(FilePath(tiff))
        check_output(
            ["pdf-compress.py", "convert", "--deskew", "--trim", "--border", tiff]
        )
        info_after = pdf_compress.do_magick_identify(FilePath(tiff))

        assert info_before["width"] == 300
        assert info_after["width"] == 311

        assert info_after["height"] == 442
        assert info_before["height"] == 430

    def test_option_enlighten_border(self):
        png = copy(tmp_png1)
        check_output(["pdf-compress.py", "convert", "--enlighten-border", png])

    def test_option_verbose(self):
        png = copy(tmp_png1)
        out = check_output(["pdf-compress.py", "--verbose", "convert", png]).decode(
            "utf-8"
        )
        assert "convert" in out
        assert ".png" in out
        assert "PixelsPerInch" in out

    def test_option_no_cleanup(self):
        def assert_no_cleanup(args, count):
            pdf = copy(tmp_pdf)
            parent_dir = Path(pdf).parent
            check_output(args + [pdf])
            files = os.listdir(parent_dir)
            assert count == len(files)

        assert_no_cleanup(["pdf-compress.py", "convert"], 4)
        assert_no_cleanup(["pdf-compress.py", "--no-cleanup", "convert"], 7)

    def test_option_ocr_input_pdf(self):
        pdf = copy(tmp_pdf)
        parent_dir = Path(pdf).parent
        check_output(["pdf-compress.py", "convert", "--ocr", pdf])
        files = os.listdir(parent_dir)
        for num in [0, 1, 2]:
            assert "test-00{}.pdf".format(num) in files
        assert len(files) == 4

    def test_option_ocr_input_jpg(self):
        jpg = copy(tmp_ocr)
        check_output(["pdf-compress.py", "convert", "--ocr", jpg])
        result = FilePath(jpg).new(extension="pdf")
        assert exists(str(result))

    def test_mutually_exclusive_options_color(self):
        process = run(
            [
                "pdf-compress.py",
                "convert",
                "--auto-color",
                "--auto-black-white",
                "test.jpg",
            ]
        )
        assert process.returncode == 2

    def test_mutually_exclusive_options_compress(self):
        process = run(
            [
                "pdf-compress.py",
                "convert",
                "--threshold",
                "50",
                "--quality",
                "50",
                "test.jpg",
            ]
        )
        assert process.returncode == 2

    ##
    # extract
    ##

    def test_extract(self):
        pdf = copy(tmp_pdf)
        parent_dir = Path(pdf).parent
        check_output(["pdf-compress.py", "extract", pdf])
        files = os.listdir(parent_dir)
        for num in [0, 1, 2]:
            assert "test-00{}.tif".format(num) in files
        assert len(files) == 4

    def test_extract_no_pdf(self):
        png = copy(tmp_png1)
        process = run(
            ["pdf-compress.py", "extract", png],
            encoding="utf-8",
            stderr=subprocess.PIPE,
        )
        assert process.returncode == 1
        assert "Specify a PDF file." in process.stderr

    ##
    # join
    ##

    def test_join(self):
        png1 = copy(tmp_png1)
        png2 = copy(tmp_png2)
        check_output(["pdf-compress.py", "join", png1, png2])
        assert exists(
            os.path.join(
                list_files.common_path((png1, png2)),
                FilePath(png1).basename + "_magick.pdf",
            )
        )

    def test_join_ocr(self):
        png1 = copy(tmp_png1)
        png2 = copy(tmp_png2)
        check_output(["pdf-compress.py", "join", "--ocr", png1, png2])
        assert exists(
            os.path.join(
                list_files.common_path((png1, png2)),
                FilePath(png1).basename + "_magick.pdf",
            )
        )

    def test_subcommand_join_convert_pdf(self):
        joined_pdf = "/tmp/jfscripts/pdf_compress/bach-busoni_300_magick.pdf"
        check_output(["pdf-compress.py", "join", tmp_png1, tmp_png2])
        assert exists(joined_pdf)
        os.remove(joined_pdf)

    def test_subcommand_join_alias(self):
        joined_pdf = "/tmp/jfscripts/pdf_compress/bach-busoni_300_magick.pdf"
        check_output(["pdf-compress.py", "jn", tmp_png1, tmp_png2])
        assert exists(joined_pdf)
        os.remove(joined_pdf)
        check_output(["pdf-compress.py", "j", tmp_png1, tmp_png2])
        assert exists(joined_pdf)
        os.remove(joined_pdf)

    ##
    # samples
    ##

    def test_real_subcommand_samples(self):
        tmp = copy(tmp_png1)
        check_output(["pdf-compress.py", "samples", tmp])
        result = (40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95)
        for threshold in result:
            suffix = "_threshold-{}.tiff".format(threshold)
            path = tmp.replace(".tiff", suffix)
            assert exists(path)

            suffix = "_quality-{}.pdf".format(threshold)
            path = tmp.replace(".pdf", suffix)
            assert exists(path)

    def test_option_subcommand_samples_on_pdf(self):
        pdf = copy(tmp_pdf)
        parent_dir = Path(pdf).parent
        check_output(["pdf-compress.py", "samples", pdf])
        files = os.listdir(parent_dir)
        assert len(files) == 30
        result = (40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95)
        for threshold in result:
            filename = "test_threshold-{}.tiff".format(threshold)
            assert filename in files

    ##
    # unify
    ##

    def test_unify_none_pdf(self):
        process = run(["pdf-compress.py", "unify", "test.jpg"])
        assert process.returncode == 1

    def test_unify_multiple_pdfs(self):
        process = run(["pdf-compress.py", "unify", "test.pdf", "test2.pdf"])
        assert process.returncode == 2

    def test_unify_real(self):
        pdf = copy(tmp_pdf)
        run(["pdf-compress.py", "unify", pdf])
        result = FilePath(pdf).new(append="_unifed")
        assert exists(str(result))

    def test_unify_margin(self):
        pdf = copy(tmp_pdf)
        run(["pdf-compress.py", "unify", "--margin", "10", pdf])
        result = FilePath(pdf).new(append="_unifed")
        assert exists(str(result))
