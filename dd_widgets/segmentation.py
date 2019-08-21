from pathlib import Path
from typing import List, Optional

from IPython.display import display

from .core import ImageTrainerMixin, img_handle
from .widgets import GPUIndex, Solver


class Segmentation(ImageTrainerMixin):
    def __init__(
        self,
        sname: str,
        *,  # unnamed parameters are forbidden
        training_repo: Path = None,
        testing_repo: Path = None,
        host: str = "localhost",
        port: int = 1234,
        gpuid: GPUIndex = 0,
        path: str = "",
        nclasses: int = -1,
        description: str = "Segmentation service",
        model_repo: Optional[str] = None,
        img_width: Optional[int] = None,
        img_height: Optional[int] = None,
        base_lr: float = 1e-3,
        db: bool = False,
        iterations: int = 10000,
        activation: str = "relu",
        dropout: float = 0.0,
        autoencoder: bool = False,
        snapshot_interval: int = 5000,
        test_interval: int = 1000,
        layers: List[str] = [],
        template: Optional[str] = None,
        mirror: bool = True,
        rotate: bool = True,
        scale: float = 1.0,
        tsplit: float = 0.0,
        finetune: bool = False,
        resume: bool = False,
        bw: bool = False,
        crop_size: int = -1,
        batch_size: int = 32,
        test_batch_size: int = 16,
        iter_size: int = 1,
        solver_type: Solver = "SGD",
        lookahead: bool = False,
        lookahead_steps: int = 6,
        lookahead_alpha: float = 0.5,
        noise_prob: float = 0.0,
        distort_prob: float = 0.0,
        # -- geometry --
        all_effects: bool = False,
        persp_horizontal: bool = False,
        persp_vertical: bool = False,
        zoom_out: bool = False,
        zoom_in: bool = False,
        pad_mode: str = "",
        persp_factor: float = 0.25,
        zoom_factor: float = 0.25,
        geometry_prob: float = 0.0,
        # -- / geometry --
        test_init: bool = False,
        class_weights: List[float] = [],
        weights: Path = None,
        model_postfix: str = "",
        tboard: Optional[Path] = None,
        ignore_label: int = -1,
        multi_label: bool = False,
        regression: bool = False,
        rand_skip: int = 0,
        timesteps: int = 32,
        unchanged_data: bool = False,
        ctc: bool = False,
        target_repository: str = "",
        loss: str = ""
    ) -> None:

        super().__init__(sname, locals())

    def display_img(self, args):
        self.output.clear_output()
        with self.output:
            for path in args["new"]:
                shape, img = img_handle(Path(path))
                if self.img_width.value == "":
                    self.img_width.value = str(shape[0])
                if self.img_height.value == "":
                    self.img_height.value = str(shape[1])
                display(
                    img
                )  # TODO display next to each other with shape info as well

                _, img = img_handle(
                    Path(path),
                    self.file_dict[Path(path)],
                    nclasses=self.nclasses.value,
                )
                display(img)
                # display(Image(path))
                # integrate THIS : https://github.com/alx/react-bounding-box
                # (cv2.imread(self.file_dict[Path(path)].as_posix()))
