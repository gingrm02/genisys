from typing import Self
from pathlib import Path
from base import Module

import jinja2

FILENAME = "preseed.cfg"

class Preseed(Module):
    def __init__(self: Self, config):
        self.config = {}
        self.config["network"] = config.getSection("Network")
        self.config["users"] = config.getSection("Users")
        self.config["apps"] = config.getSection("Applications")
    # end __init__

    def install_location(self: Self) -> Path:
        ftp_dir = Path(self.config["network"]["tftp_directory"])
        return Path(ftp_dir, FILENAME)
    # end install_location

    def generate(self: Self) -> str:
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))
        template = jinja_env.get_template("preseed.cfg.jinja2")
        return template.render(settings=self.config["users"])
    # end generate