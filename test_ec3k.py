import json
from pathlib import Path

import ec3k


class TestEnergyCount3KState:
	def test_capture_fields_accepts_subprocess_bytes(self):
		fields = ec3k.capture_fields(b'data d4 01 8c 7e\n')
		assert fields == ['data', 'd4', '01', '8c', '7e']

	def test_basic(self):
		hex_bytes = [
			'ca', 'ff', '9c', 'e0', '66', '10', '34', '6d', '3a', '83', '53',
			'12', 'fe', 'c0', 'f5', '09', '4c', '76', '07', '3d', '16', '29',
			'96', '8f', '75', '1d', '93', '7e', '54', 'cf', '1e', 'c2', '36',
			'17', '2f', '2c', '0e', '12', 'cd', '8f', '14', '8e', '77', '1e',
			'f1', 'ca', 'ce', 'e3', '23', 'e9', '05', 'ce', '74', 'aa', 'da',
			'52', '62', 'a5', 'b1', 'a3', '58', '4e', 'bd', 'ae', 'c4', '77',
			'e9', '89', 'a0',
		]

		state = ec3k.EnergyCount3KState(hex_bytes)

		assert state.id == 0xf100
		assert state.time_total == 36725
		assert state.time_on == 6006
		assert state.energy == 138854
		assert state.power_current == 0.0
		assert state.power_max == 86.8
		assert state.reset_counter == 5
		assert not state.device_on_flag
		assert state.to_tsv().split('\t')[1:] == [
			'f100', '36725', '6006', '138854', '0.0', '86.8', '5'
		]

		assert state.time_total == state.uptime
		assert state.time_on == state.since_reset
		assert state.energy_1 == state.energy
		assert state.energy_2 == state.energy * 16
		assert state.current_power == state.power_current
		assert state.max_power == state.power_max

	def test_decode_log(self):
		total = valid = invalid = 0
		last_state = None
		path = Path(__file__).with_name('tests.json')

		with path.open() as packets:
			for line in packets:
				total += 1
				hex_bytes = json.loads(line)
				try:
					state = ec3k.EnergyCount3KState(hex_bytes)
				except ec3k.InvalidPacket:
					invalid += 1
					continue

				if last_state is not None:
					assert state.time_total >= last_state.time_total
					assert state.time_on >= last_state.time_on
					assert state.energy >= last_state.energy
					assert state.reset_counter >= last_state.reset_counter

				assert state.power_max <= 4.0
				assert state.power_current <= state.power_max
				last_state = state
				valid += 1

		assert total == 6151
		assert valid == 5978
		assert invalid == 173

	def test_decode_rtl_fm_packet(self):
		packet = bytes.fromhex(
			'9d c6 ff 00 00 00 0f 00 00 00 00 00 03 32 0c a0 38 82 77 98 '
			'61 39 87 7f d8 72 fd 87 84 43 de 00 00 00 04 a3 de 01 80 a1 24')

		state = ec3k.EnergyCount3KState.from_rtl_fm_packet(packet)

		assert state.id == 0xdc6f
		assert state.power_current == 90.4
		assert state.power_max == 1010.5
		assert state.energy == 19867574474
		assert state.time_total == 64942080
		assert state.time_on == 64942080
		assert state.reset_counter == 1
		assert state.device_on_flag
