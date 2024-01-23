from . import hotplug
from .decorators import *
import tuned.logs
from tuned.utils.commands import commands

import os
import fnmatch

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
		log.error("Intel UNCORE INIT")
		self._devices_supported = True
		self._assigned_devices = set()
		self._free_devices = set()

		devices = os.listdir(sysfs_dir)
		print("AAAAAAA", devices)

		# For new TPMI interface use only uncore devices
		tpmi_devices = fnmatch.filter(devices, 'uncore*')
		print("BBBBBB", tpmi_devices)
		if len(tpmi_devices) > 0:
			devices = tpmi_devices

		for dev in devices:
			self._free_devices.add(dev)

	def _instance_init(self, instance):
		instance._has_static_tuning = True
		instance._has_dynamic_tuning = False

		for device in instance._assigned_devices:
			log.error("INSTANCE INIT" + sysfs_dir + "%s" % device)

	def _instance_cleanup(self, instance):
		for device in instance._assigned_devices:
			log.error("INSTANCE CLEANUP" + sysfs_dir + "%s" % device)
		pass

	def _device_module_name(self, device):
		return "intel_uncore_frequency"

	def _get_khz(self, device, file):
		sysfs_file = sysfs_dir + device + "/" + file
		khz = cmd.read_file(sysfs_file, no_error=ignore_missing)
		if len(khz) > 0:
			return int(khz)
		return None

	def _set_khz(self, device, file, khz):
		sysfs_file = sysfs_dir + device + "/" + file
		cmd.write_to_file(sysfs_file, "%u" % khz, no_error=ignore_missing)
		return khz

	@classmethod
	def _get_config_options(cls):
		# TODO other options
		return {
			# "uncore_max_freq_khz": 0,
			"uncore_max_freq_khz_delta": 0,
			# "uncore_max_freq_khz_procent": 0,
		}

	# @command_set("uncore_max_freq_khz", per_device = True)
	# def _set_uncore_max_freq_khz(self, value, device, sim):
	# 	print("SET ", device, value)
	# 	try:
	# 		freq_khz = int(value)
	# 	except ValueError:
	# 		log.error("uncore_max_freq_khz value '%s' is not integer" % value)
	# 		return None
	#
	# 	# TODO exceptions
	# 	max_khz = self._get_khz(device, "initial_max_freq_khz")
	# 	min_khz = self._get_khz(device, "initial_min_freq_khz")
	#
	# 	if freq_khz < min_khz or freq_khz > max_khz:
	# 		log.error("uncore_max_freq_khz value %d is not in range [%d %d]" % (freq_khz, min_khz, max_khz))
	# 		return None
	#
	# 	if sim:
	# 		return freq_khz
	#
	# 	return self._set_khz(device, "max_freq_khz", freq_khz)
	#
	# @command_get("uncore_max_freq_khz")
	# def _get_uncore_max_freq_khz(self, device, ignore_missing=False):
	# 	file = sysfs_dir + device + "/max_freq_khz"
	# 	value = cmd.read_file(file, no_error=ignore_missing)
	# 	print("GET ", device, value)
	# 	if len(value) > 0:
	# 		return value
	# 	return None

	@command_set("uncore_max_freq_khz_delta", per_device = True)
	def _set_uncore_max_freq_khz_delta(self, value, device, sim):
		print("SET DELTA ", device, value)
		try:
			delta = int(value)
		except ValueError:
			log.error("uncore_max_freq_khz_delta value '%s' is not integer" % value)
			return None

		# TODO exceptions
		# TODO make this commont code
		max_khz = self._get_khz(device, "initial_max_freq_khz")
		min_khz = self._get_khz(device, "initial_min_freq_khz")
		freq_khz = max_khz - delta

		if freq_khz < min_khz or freq_khz > max_khz:
			log.error("uncore_max_freq_khz value %d is not in range [%d %d]" % (freq_khz, min_khz, max_khz))
			return None

		if sim:
			return freq_khz

		return self._set_khz(device, "max_freq_khz", freq_khz)

	@command_get("uncore_max_freq_khz_delta")
	def _get_uncore_max_freq_khz_delta(self, device, ignore_missing=False):

		max_khz = self._get_khz(device, "initial_max_freq_khz")
		freq_khz = self._get_khz(device, "max_freq_khz")

		delta = max_khz - freq_khz
		print("GET DELTA", device, delta)
		return delta
