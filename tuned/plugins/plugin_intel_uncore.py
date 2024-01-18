from . import hotplug
from .decorators import *
import tuned.logs
from tuned.utils.commands import commands

import os
import fnmatch

log = tuned.logs.get()
cmd = commands()

SYSFS_DIR = "/sys/devices/system/cpu/intel_uncore_frequency/"

class IntelUncorePlugin(hotplug.Plugin):
	"""
	`intel_uncore`::

	----
	[intel_uncore]
	max_freq_khz_delta=200000
	----
	Limit the maximum uncore frequency that hardware will use. This value is in
	Kilo Hertz units. Delta value specifies an offset from the default uncore maximum
	frequency. For example, the value of 200000 means that maximum uncore frequency
	will be capped to the default uncore maximum frequency minus 200 MHz.
	====
	"""

	def _init_devices(self):
		self._devices_supported = True
		self._assigned_devices = set()
		self._free_devices = set()
		self._is_tpmi = False

		try:
			devices = os.listdir(SYSFS_DIR)
		except OSError:
			return

		# For new TPMI interface use only uncore devices
		tpmi_devices = fnmatch.filter(devices, 'uncore*')
		if len(tpmi_devices) > 0:
			self._is_tpmi = True  # Not used at present but can be usefull in future
			devices = tpmi_devices

		for d in devices:
			self._free_devices.add(d)

		log.debug("devices: %s", str(self._free_devices))

	def _instance_init(self, instance):
		instance._has_static_tuning = True
		instance._has_dynamic_tuning = False

	def _instance_cleanup(self, instance):
		pass

	def _device_module_name(self, device):
		return "intel_uncore_frequency"

	def _get(self, dev_dir, file):
		sysfs_file = SYSFS_DIR + dev_dir + "/" + file
		value = cmd.read_file(sysfs_file)
		if len(value) > 0:
			return int(value)
		return None

	def _set(self, dev_dir, file, value):
		sysfs_file = SYSFS_DIR + dev_dir + "/" + file
		if cmd.write_to_file(sysfs_file, "%u" % value):
			return value
		return None

	@classmethod
	def _get_config_options(cls):
		# TODO other options ?
		return {
			# "uncore_max_freq_khz": 0,
			"max_freq_khz_delta": 0,
			# "uncore_max_freq_khz_procent": 0,
		}

	@command_set("max_freq_khz_delta", per_device = True)
	def _set_max_freq_khz_delta(self, value, device, sim):
		try:
			delta = int(value)
		except ValueError:
			log.error("max_freq_khz_delta value '%s' is not integer" % value)
			return None

		try:
			initial_max_freq_khz = self._get(device, "initial_max_freq_khz")
			initial_min_freq_khz = self._get(device, "initial_min_freq_khz")
		except (OSError, IOError):
			log.error("fail to read uncore frequency values")
			return None

		max_delta = initial_max_freq_khz - initial_min_freq_khz
		if delta > max_delta:
			log.error("delta value %d below allowable frequency range [%d %d], max delta %d"
					  % (delta, initial_min_freq_khz, initial_max_freq_khz, max_delta))
			return None

		if sim:
			return delta

		max_freq_khz = initial_max_freq_khz - delta
		log.debug("%s: set max_freq_khz %d (delta %d)" % (device, max_freq_khz, delta))

		return self._set(device, "max_freq_khz", max_freq_khz)

	@command_get("max_freq_khz_delta")
	def _get_max_freq_khz_delta(self, device, ignore_missing=False):
		if ignore_missing and not os.path.isdir(SYSFS_DIR):
			return None

		try:
			inital_max_freq_khz = self._get(device, "initial_max_freq_khz")
			max_freq_khz = self._get(device, "max_freq_khz")
		except (OSError, IOError):
			log.error("fail to read uncore frequency values")
			return None

		delta = inital_max_freq_khz - max_freq_khz
		log.debug("%s: get max_freq_khz %d (delta %d)" % (device, max_freq_khz, delta))

		return delta
