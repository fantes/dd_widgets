from pathlib import Path
from typing import List, Optional, Union

from IPython.display import display

from ipywidgets import HBox, Button

from .core import ImageTrainerMixin, img_handle, sample_from_iterable
from .widgets import MLWidget, Solver


class Detection(MLWidget, ImageTrainerMixin):
    ctc = False

    def display_img(self, args):
        self.output.clear_output()
        with self.output:
            for path in args["new"]:
                shape, img = img_handle(Path(path))
                if self.img_width.value == "":
                    self.img_width.value = str(shape[0])
                if self.img_height.value == "":
                    self.img_height.value = str(shape[1])
                _, img = img_handle(Path(path), bbox=self.file_dict[Path(path)])
                display(img)

    def update_train_file_list(self, *args):
        with self.output:
            self.file_dict = {
                Path(x.split()[0]): Path(x.split()[1])
                for x in Path(self.training_repo.value).read_text().split("\n")
                if len(x.split()) >= 2
            }

            self.file_list.options = [
                fh.as_posix()
                for fh in sample_from_iterable(self.file_dict.keys(), 10)
            ]

    def update_test_file_list(self, *args):
        with self.output:
            self.file_dict = {
                Path(x.split()[0]): Path(x.split()[1])
                for x in Path(self.testing_repo.value).read_text().split("\n")
                if len(x.split()) >= 2
            }

            self.file_list.options = [
                fh.as_posix()
                for fh in sample_from_iterable(self.file_dict.keys(), 10)
            ]

    def __init__(
        self,
        sname: str,
        *,  # unnamed parameters are forbidden
        training_repo: Path = None,
        testing_repo: Path = None,
        host: str = "localhost",
        port: int = 1234,
        path: str = "",
        nclasses: int = -1,
        description: str = "Detection service",
        model_repo: Optional[str] = None,
        img_width: Optional[int] = None,
        img_height: Optional[int] = None,
        db_width: int = 0,
        db_height: int = 0,
        base_lr: float = 1e-4,
        iterations: int = 10000,
        snapshot_interval: int = 5000,
        test_interval: int = 1000,
        gpuid: Union[int, List[int]] = 0,
        layers: List[str] = [],
        template: Optional[str] = None,
        mirror: bool = False,
        rotate: bool = False,
        tsplit: float = 0.0,
        finetune: bool = False,
        resume: bool = False,
        bw: bool = False,
        crop_size: int = -1,
        batch_size: int = 32,
        test_batch_size: int = 16,
        iter_size: int = 1,
        solver_type: Solver = "SGD",
        noise_prob: float = 0.001,
        distort_prob: float = 0.5,
        test_init: bool = False,
        class_weights: List[float] = [],
        weights: Path = None,
        tboard: Optional[Path] = None,
        ignore_label: int = -1,
        multi_label: bool = False,
        regression: bool = False,
        rand_skip: int = 0,
        timesteps: int = 32,
        unchanged_data: bool = False,
        target_repository: str = "",
        ctc: bool = False
    ) -> None:

        super().__init__(sname, locals())

        self.train_labels = Button(
            description=Path(self.training_repo.value).name  # type: ignore
        )
        self.test_labels = Button(
            description=Path(self.testing_repo.value).name  # type: ignore
        )

        self.train_labels.on_click(self.update_train_file_list)
        self.test_labels.on_click(self.update_test_file_list)

        self.file_list.observe(self.display_img, names="value")

        self._img_explorer.children = [
            HBox([HBox([self.train_labels, self.test_labels])]),
            self.file_list,
            self.output,
        ]

        self.update_label_list(())