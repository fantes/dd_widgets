# fmt: off

import json
import logging
import time
from collections import OrderedDict
from enum import Enum
from inspect import signature
from pathlib import Path
from typing import Any, Dict, get_type_hints

import requests
from ipywidgets import (HTML, Button, Checkbox, Dropdown, FloatText, HBox,
                        IntProgress, IntText, Label, Layout, Output,
                        SelectMultiple, Tab)
from ipywidgets import Text as TextWidget
from ipywidgets import VBox

from .loghandler import OutputWidgetHandler

# fmt: on

widget_output_handler = OutputWidgetHandler()
sname_url = "http://{host}:{port}/{path}/services/{sname}"


class Solver(Enum):
    SGD = "SGD"
    ADAM = "ADAM"
    RMSPROP = "RMSPROP"
    AMSGRAD = "AMSGRAD"
    ADAGRAD = "ADAGRAD"
    ADADELTA = "ADADELTA"
    NESTEROV = "NESTEROV"


class SolverDropdown(Dropdown):
    def __init__(self, *args, **kwargs):
        Dropdown.__init__(
            self, *args, options=list(e.name for e in Solver), **kwargs
        )


# -- Core 'abstract' widget for many tasks


class MLWidget(object):

    _fields = {  # typing: Dict[str, str]
        "sname": "Model name",
        "training_repo": "Training directory",
        "testing_repo": "Testing directory",
    }

    _widget_type = {
        int: IntText,
        float: FloatText,
        bool: Checkbox,
        Solver: SolverDropdown,
    }

    # host: TextWidget
    # port: TextWidget

    def typing_info(self, local_vars: Dict[str, Any]):
        fun = self.__init__  # type: ignore
        typing_dict = get_type_hints(fun)
        for param in signature(fun).parameters.values():
            if param.name != "sname":
                yield (
                    param.name,
                    eval(param.name, local_vars),
                    typing_dict[param.name],
                )

    def __init__(self, sname: str, local_vars: Dict[str, Any], *args) -> None:

        # logger.addHandler(log_viewer(self.output),)

        self.sname = sname
        self.output = Output(layout=Layout(max_width="650px"))
        self.pbar = IntProgress(
            min=0,
            max=100,
            description="Progression:",
            layout=Layout(margin="18px"),
        )
        self.run_button = Button(description="Run training")
        self.info_button = Button(description="Info")
        self.stop_button = Button(description="Stop training")
        self.hardclear_button = Button(description="Hard clear")

        self._widgets = [  # typing: List[Widget]
            HTML(
                value="<h2>{task} task: {sname}</h2>".format(
                    task=self.__class__.__name__, sname=self.sname
                )
            ),
            HBox([self.run_button, self.stop_button]),
            HBox([self.info_button, self.hardclear_button]),
        ]

        self.run_button.on_click(self.run)
        self.info_button.on_click(self.info)
        self.stop_button.on_click(self.stop)
        self.hardclear_button.on_click(self.hardclear)

        for name, value, type_hint in self.typing_info(local_vars):
            self._add_widget(name, value, type_hint)

        self._configuration = VBox(
            self._widgets, layout=Layout(min_width="250px")
        )

        self._tabs = Tab(layout=Layout(height=""))
        self._output = VBox([self.pbar, self._tabs])
        self._main_elt = HBox(
            [self._configuration, self._output], layout=Layout(width="1200px")
        )
        self._img_explorer = VBox(
            [self.output], layout=Layout(min_height="800px", width="590px")
        )

        self._tabs.children = [self._img_explorer, widget_output_handler.out]
        self._tabs.set_title(0, "Exploration")
        self._tabs.set_title(1, "Logs")

        self.file_list = SelectMultiple(
            options=[],
            value=[],
            rows=10,
            description="File list",
            layout=Layout(height="200px", width="560px"),
        )

    def _add_widget(self, name, value, type_hint):

        widget_type = self._widget_type.get(type_hint, None)

        if widget_type is None:
            setattr(
                self,
                name,
                TextWidget(  # Widget type by default then convert to str
                    value="" if value is None else str(value),
                    layout=Layout(min_width="20ex", margin="-2px 2px 4px 2px"),
                ),
            )
            self._widgets.append(
                VBox(
                    [
                        Label(self._fields.get(name, name) + ":"),
                        getattr(self, name),
                    ]
                )
            )
        else:
            setattr(
                self,
                name,
                widget_type(
                    value=type_hint() if value is None else (value),
                    layout=Layout(width="100px", margin="4px 2px 4px 2px"),
                ),
            )

            self._widgets.append(
                HBox(
                    [
                        Label(
                            self._fields.get(name, name),
                            layout=Layout(min_width="180px"),
                        ),
                        getattr(self, name),
                    ],
                    layout=Layout(margin="4px 2px 4px 2px"),
                )
            )

    def _ipython_display_(self):
        self._main_elt._ipython_display_()

    def stop(self, *_):
        self.output.clear_output()
        with self.output:
            request = sname_url.format(
                host=self.host.value,
                port=self.port.value,
                path=self.path.value,
                sname=self.sname,
            )
            c = requests.delete(request)
            logging.info(
                "Stop service {sname}: {json}".format(
                    sname=self.sname, json=json.dumps(c.json(), indent=2)
                )
            )

            print(json.dumps(c.json(), indent=2))
            return c.json()

    def hardclear(self, *_):
        # The basic version
        self.output.clear_output()
        with self.output:
            MLWidget.create_service(self)
            request = (sname_url + "?clear=full").format(
                host=self.host.value,
                port=self.port.value,
                path=self.path.value,
                sname=self.sname,
            )
            c = requests.delete(request)
            logging.info(
                "Clearing (full) service {sname}: {json}".format(
                    sname=self.sname, json=json.dumps(c.json(), indent=2)
                )
            )

            print(json.dumps(c.json(), indent=2))
            # return c.json()

    def create_service(self, *_):
        with self.output:
            host = self.host.value
            port = self.port.value

            body = OrderedDict(
                [
                    ("mllib", "caffe"),
                    ("description", self.sname),
                    ("type", "supervised"),
                    (
                        "parameters",
                        {
                            "mllib": {"nclasses": 42},  # why not?
                            "input": {"connector": "csv"},
                        },
                    ),
                    (
                        "model",
                        {
                            "repository": self.model_repo.value,
                            "create_repository": True,
                            # "templates": "../templates/caffe/"
                        },
                    ),
                ]
            )

            logging.info(
                "Creating service '{sname}':\n {body}".format(
                    sname=self.sname, body=json.dumps(body, indent=2)
                )
            )
            c = requests.put(
                sname_url.format(
                    host=host, port=port, path=self.path.value, sname=self.sname
                ),
                json.dumps(body),
            )

            if c.json()["status"]["code"] != 201:
                logging.warning(
                    "Reply from creating service '{sname}': {json}".format(
                        sname=self.sname, json=json.dumps(c.json(), indent=2)
                    )
                )
            else:
                logging.info(
                    "Reply from creating service '{sname}': {json}".format(
                        sname=self.sname, json=json.dumps(c.json(), indent=2)
                    )
                )

            print(json.dumps(c.json(), indent=2))

            return c.json()

    def run(self, *_):
        logging.info("Entering run method")
        self.output.clear_output()

        with self.output:
            host = self.host.value
            port = self.port.value
            body = self._create_service_body()

            logging.info(
                "Sending request "
                + sname_url.format(
                    host=host, port=port, path=self.path.value, sname=self.sname
                )
            )
            c = requests.get(
                sname_url.format(
                    host=host, port=port, path=self.path.value, sname=self.sname
                )
            )
            logging.info(
                "Current state of service '{sname}': {json}".format(
                    sname=self.sname, json=json.dumps(c.json(), indent=2)
                )
            )
            if c.json()["status"]["msg"] != "NotFound":
                # self.clear()
                logging.warning(
                    (
                        "Since service '{sname}' was still there, "
                        "it has been fully cleared: {json}"
                    ).format(
                        sname=self.sname, json=json.dumps(c.json(), indent=2)
                    )
                )

            logging.info(
                "Creating service '{sname}':\n {body}".format(
                    sname=self.sname, body=json.dumps(body, indent=2)
                )
            )
            c = requests.put(
                sname_url.format(
                    host=host, port=port, path=self.path.value, sname=self.sname
                ),
                json.dumps(body),
            )

            if c.json()["status"]["code"] != 201:
                logging.warning(
                    "Reply from creating service '{sname}': {json}".format(
                        sname=self.sname, json=json.dumps(c.json(), indent=2)
                    )
                )
                return
            else:
                logging.info(
                    "Reply from creating service '{sname}': {json}".format(
                        sname=self.sname, json=json.dumps(c.json(), indent=2)
                    )
                )

            body = self._train_body()

            logging.info(
                "Start training phase: {body}".format(
                    body=json.dumps(body, indent=2)
                )
            )
            c = requests.post(
                "http://{host}:{port}/{path}/train".format(
                    host=host, port=port, path=self.path.value
                ),
                json.dumps(body),
            )
            logging.info(
                "Reply from training service '{sname}': {json}".format(
                    sname=self.sname, json=json.dumps(c.json(), indent=2)
                )
            )

            print(json.dumps(c.json(), indent=2))

            self.value = self.iterations.value
            self.pbar.bar_style = "info"
            self.pbar.max = self.iterations.value

            while True:
                info = self.info(print_output=False)
                self.pbar.bar_style = ""

                status = info["head"]["status"]

                if status == "finished":
                    self.pbar.value = self.iterations.value
                    self.pbar.bar_style = "success"
                    break

                self.pbar.value = info["body"]["measure"].get("iteration", 0)

                time.sleep(1)

    def info(self, print_output=True):
        with self.output:
            # TODO job number
            request = (
                "http://{host}:{port}/{path}/train?service={sname}&"
                "job=1&timeout=10".format(
                    host=self.host.value,
                    port=self.port.value,
                    path=self.path.value,
                    sname=self.sname,
                )
            )
            c = requests.get(request)
            logging.info(
                "Getting info for service {sname}: {json}".format(
                    sname=self.sname, json=json.dumps(c.json(), indent=2)
                )
            )
            if print_output:
                print(json.dumps(c.json(), indent=2))
            return c.json()

    def update_label_list(self, _):
        with self.output:
            if self.training_repo.value != "":
                self.train_labels.options = tuple(
                    sorted(
                        f.stem for f in Path(self.training_repo.value).glob("*")
                    )
                )
            if self.testing_repo.value != "":
                self.test_labels.options = tuple(
                    sorted(
                        f.stem for f in Path(self.testing_repo.value).glob("*")
                    )
                )

            self.train_labels.rows = min(10, len(self.train_labels.options))
            self.test_labels.rows = min(10, len(self.test_labels.options))
            if self.nclasses.value == -1:
                self.nclasses.value = str(len(self.train_labels.options))