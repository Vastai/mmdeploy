# Copyright (c) OpenMMLab. All rights reserved.
import logging
import os.path as osp
import sys
from typing import Any, Callable, Optional, Sequence

from mmdeploy.utils import get_backend_config, get_root_logger
from ..base import BACKEND_MANAGERS, BaseBackendManager
from mmdeploy.utils import (get_common_config, get_normalization, get_calib_config,
                            get_onnx_config, get_partition_config, get_model_inputs,
                            get_quantization_config, get_root_logger, load_config)

@BACKEND_MANAGERS.register('vacc')
class VACCManager(BaseBackendManager):

    @classmethod
    def build_wrapper(cls,
                      backend_files: Sequence[str],
                      device: str = 'cpu',
                      input_names: Optional[Sequence[str]] = None,
                      output_names: Optional[Sequence[str]] = None,
                      deploy_cfg: Optional[Any] = None,
                      **kwargs):
        """Build the wrapper for the backend model.

        Args:
            backend_files (Sequence[str]): Backend files.
            device (str, optional): The device info. Defaults to 'cpu'.
            input_names (Optional[Sequence[str]], optional): input names.
                Defaults to None.
            output_names (Optional[Sequence[str]], optional): output names.
                Defaults to None.
            deploy_cfg (Optional[Any], optional): The deploy config. Defaults
                to None.
        """
        from .wrapper import VACCWrapper

        # For unittest deploy_config will not pass into _build_wrapper
        # function.
        backend_config = get_backend_config(deploy_cfg)

        return VACCWrapper(
            deploy_cfg=deploy_cfg,
            output_names=output_names)

    @classmethod
    def is_available(cls, with_custom_ops: bool = False) -> bool:
        """Check whether backend is installed.

        Args:
            with_custom_ops (bool): check custom ops exists.
        Returns:
            bool: True if backend package is installed.
        """
        import importlib

        has_vacc = importlib.util.find_spec('vacc') is not None
        has_tvm = importlib.util.find_spec('tvm') is not None
        ret = has_vacc and has_tvm

        return ret

    @classmethod
    def get_version(cls) -> str:
        """Get the version of the backend."""
        if not cls.is_available():
            return 'None'
        else:
            import pkg_resources
            try:
                return pkg_resources.get_distribution('vacc').version
            except Exception:
                return 'None'

    @classmethod
    def check_env(cls, log_callback: Callable = lambda _: _) -> str:
        """Check current environment.

        Returns:
            str: Info about the environment.
        """
        info = super().check_env(log_callback=log_callback)
        available = cls.is_available()
        ops_available = cls.is_available(with_custom_ops=True)
        ops_available = 'Available' if ops_available else 'NotAvailable'

        if available:
            ops_info = f'vacc custom ops:\t{ops_available}'
            log_callback(ops_info)
            info = f'{info}\n{ops_info}'

        return info

    @classmethod
    def to_backend(cls,
                   ir_files: Sequence[str],
                   work_dir: str,
                   deploy_cfg: Any,
                   log_level: int = logging.INFO,
                   device: str = 'cpu',
                   **kwargs) -> Sequence[str]:
        """Convert intermediate representation to given backend.

        Args:
            ir_files (Sequence[str]): The intermediate representation files.
            work_dir (str): The work directory, backend files and logs should
                be saved in this directory.
            deploy_cfg (Any): The deploy config.
            log_level (int, optional): The log level. Defaults to logging.INFO.
            device (str, optional): The device type. Defaults to 'cpu'.
        Returns:
            Sequence[str]: Backend files.
        """
        logger = get_root_logger()

        import copy
        from . import is_available

        if not is_available():
            logger.error('vacc and tvm support is not available, please make sure:\n'
                         '1) `vacc/python` and `tvm/python` existed in `PYTHONPATH`\n'
                         '2) python import tvm and import vacc success')
            sys.exit(1)

        from .onnx2vacc import from_onnx
        model_inputs = get_model_inputs(deploy_cfg)

        backend_files = []
        for model_id, onnx_path in zip(range(len(ir_files)), ir_files):
            model_input = copy.deepcopy(model_inputs[model_id])
            # pre_fix_name = osp.splitext(osp.split(onnx_path)[1])[0]
            # output_path = osp.join(work_dir, pre_fix_name)
            model_file = from_onnx(onnx_path, work_dir, model_input, deploy_cfg)
            backend_files += model_file

        return backend_files
