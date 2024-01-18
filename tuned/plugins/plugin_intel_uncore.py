from . import hotplug
from .decorators import *
import tuned.logs
from tuned.utils.commands import commands

import os

# TODO make this parameter
ignore_missing = False

log = tuned.logs.get()
cmd = commands()
sysfs_dir = "/sys/devices/system/cpu/intel_uncore_frequency/"

class IntelUncorePlugin(hotplug.Plugin):
	"""
	`intel_uncore`::

	----
	[intel_uncore]
	uncore_max_freq_khz_delta=200000
	----
	Limit the maximum uncore frequency that hardware will use. This value is in
	Kilo Hertz units. Delta value specifies an offset from the default uncore maximum
	frequency. For example, the value of 200000 means that maximum uncore frequency
	will be capped to the default uncore maximum frequency minus 200 MHz.
	====
	"""

	def _init_devices(self):
		log.info("Intel UNCORE INIT")
		self._devices_supported = True
		self._assigned_devices = set()
		self._free_devices = set()

		for device in os.listdir(sysfs_dir):
			self._free_devices.add(device)

	def _instance_init(self, instance):
		instance._has_static_tuning = True
		instance._has_dynamic_tuning = False

		# for device in instance._assigned_devices:
		# 	log.info("INSTANCE INIT" + sysfs_dir + "%s" % device)

	def _instance_cleanup(self, instance):
		# for device in instance._assigned_devices:
		#	log.info("INSTANCE CLEANUP" + sysfs_dir + "%s" % device)
		pass

	def _device_module_name(self, device):
		return "intel_uncore_frequency"

	def _get_khz(self, device, value):
		file = sysfs_dir + device + "/" + value
		khz = cmd.read_file(file, no_error=ignore_missing)
		if len(khz) > 0:
			return int(khz)
		return None

	@classmethod
	def _get_config_options(cls):
		# TODO other options
		return {
			"uncore_max_freq_khz": 0,
			# "uncore_max_freq_khz_delta": 0,
			# "uncore_max_freq_khz_procent": 0,
		}

	@command_set("uncore_max_freq_khz", per_device = True)
	def _set_uncore_max_freq_khz(self, value, device, sim):
		print("SET ", device, value)
		try:
			freq_khz = int(value)
		except ValueError:
			log.error("uncore_max_freq_khz value '%s' is not integer" % value)
			return None

		# TODO exceptions
		max_khz = self._get_khz(device, "initial_max_freq_khz")
		min_khz = self._get_khz(device, "initial_min_freq_khz")

		if freq_khz < min_khz or freq_khz > max_khz:
			log.error("uncore_max_freq_khz value %d is not in range [%d %d]" % freq_khz, min_khz, max_khz)
			return None

		if freq_khz > 0:
			file = sysfs_dir + device + "/max_freq_khz"
			if not sim:
				cmd.write_to_file(file, "%d" % freq_khz)
			return freq_khz
		else:
			return None

	@command_get("uncore_max_freq_khz")
	def _get_uncore_max_freq_khz(self, device, ignore_missing=False):
		file = sysfs_dir + device + "/max_freq_khz"
		value = cmd.read_file(file, no_error=ignore_missing)
		if len(value) > 0:
			return value
		return None
