#!/usr/bin/env python3
"""Software receiver for EnergyCount 3000
Copyright (C) 2013  Gasper Zejn

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
from optparse import OptionParser
import os
import struct
import time

BUFFSIZE = 4096
MOD_UNKNOWN = 2
MOD_BINARY  = 5

MIN_BREAK = 100

verbose = False

def log(msg):
	if verbose:
		sys.stderr.write(msg + "\n")

class Packet:
	TRIM = 10
	expected_bit_size = 4
	
	def __init__(self):
		self.data = []
		self.len = 0
		self.start = -1
		self.ntran = 0
		self.breaklen = 0
		
		self.decoded = ''
		self.bitcount = 0
		self.cp = 0
		self.modulation = MOD_UNKNOWN
		
		self.leader_edges = 0
		self.trailer_edges = 0
		self.bits = 0
	
	def __repr__(self):
		return 'Packet: len=%s ntran=%s' % (len(self.data), self.ntran)
	
	def push_bit(self, val):
		assert val in (1,0)
		self.bits = self.bits << 1 | val
	
	def trim(self, data):
		
		if len(data) <= self.expected_bit_size:
			return []
		
		if len(set(data[:self.expected_bit_size])) == 1:
			# start is ok
			start = 0
		else:
			# remove grass
			start = self.expected_bit_size
			for i in [3,2,1]:
				if data[start] == data[i]:
					start = i
				else:
					break
		
		if len(set(data[-self.expected_bit_size:])) == 1:
			end = 0
		else:
			end = self.expected_bit_size
			for i in [3,2,1]:
				if data[-end] == data[-i]:
					end = i
				else:
					break
		if start:
			data = data[start:]
		if end:
			data = data[:-end]
		return data
	
	def old_trim(self, data):
		start = self.TRIM
		for i, v in enumerate(data):
			if i < start:
				pv = v
				continue
			if pv == v:
				start = i+1
			else:
				break
		
		stop = self.TRIM
		for i, v in enumerate(reversed(data)):
			if i < stop:
				pv = v
				continue
			if pv == v:
				stop = i + 1
			else:
				break
		return data[start:-stop]
	
	def recover_clock(self):
		cp = None
		
		#print ''.join([str(i) for i in self.data]).replace('0', '.')
		
		if len(self.data) < 50:
			return False
		
		pt = 0
		# find shortest pulse length in packet
		for tt, v in enumerate(self.trim(self.data)):
			if tt == 0:
				pv = v
			t = tt+1
			if pv != v:
				pl = t - pt
				#print pl, 'from', pt, 'to', t, pv, '->', v
				if pl < 2:
					log('pulse too short %d' % (pl,))
					return False
				if cp is None:
					cp = pl
				if pl < cp:
					cp = pl
				pv = v
				pt = t
		
		if cp is None:
			return False
		
		cp = float(cp)
		#print 'cp estimate = %s' % cp
		v = self.data[0]
		# adjust clock
		pt = 0
		for tt, v in enumerate(self.trim(self.data)):
			if tt == 0:
				pv = v
			t = tt+1
			if pv != v:
				pl = t - pt
				if (pl < cp):
					cp = (cp*2.0 + pl) / 3.0
				elif pl > cp:
					r = pl / cp
					#print pl, cp
					n = round(r)
					e = abs((r-n)/n)
					if e > 0.4:
						#print e
						log('inconsistent pulse length')
						return False
					if n > 20:
						log('too many consecutive same bits')
						return False
					cp = (cp*2.0 + pl/n) / 3.0
				pv = v
				pt = t
		
		#print 'cp got = %s' % cp
		# decode bits
		pt = 0
		for tt, v in enumerate(self.trim(self.data)):
			if tt == 0:
				pv = v
			t = tt+1
			if pv != v:
				pl = t - pt
				
				r = pl / cp
				nbits = int(round(r))
				
				for n in range(nbits):
					self.push_bit(pv)
				pv = v
				pt = t
		
		hd = iter('%x' % self.bits)
		h = ' '.join(['%s%s' % i for i in zip(hd, hd)])
		print('data', h, flush=True)

class Packetizer:
	
	def __init__(self):
		self.sample_cnt = 0
		self.pv = 0
		self.packet = None
		self.data = b""
	
	def feed(self, data):
		self.data = self.data + data
		
		for packet in self._nextpacket():
			yield packet
	
	def _nextpacket(self):
		datalen = len(self.data)
		i = 0
		
		if self.packet is None:
			self.packet = Packet()
		
		packet = self.packet
		inpacket = bool(packet.data)
		breaklen = 0
		
		while i < datalen:
			v = self.data[i] >= 190 and 1 or 0
			
			if v != self.pv:
				inpacket = True
				self.pv = v
				packet.ntran += 1
				# breaklen XXX
				breaklen = 0
			else:
				breaklen += 1
			
			if inpacket:
				packet.data.append(v)
				# ce je break
				if breaklen > MIN_BREAK:
					# trim break and return packet
					packet.data = packet.data[:len(packet.data)-breaklen]
					if packet.data:
						packet.data = packet.data[:-1]
					if packet.data:
						yield packet
					self.packet = packet = Packet()
					inpacket = False
			
			i += 1
		self.data = b''
		

class RtlFmPacketizer:
	"""Recover EC3K packets from the signed 16-bit output of rtl_fm -A fast."""
	LEVEL_THRESHOLD = 47
	BITTIME = 10
	BITTIME_BOUND_LOWER = 9
	BITTIME_BOUND_UPPER = 11
	PACKET_MIN_BITS = 100

	def __init__(self):
		self.bits = []
		self.last_level = 0
		self.last_edge = 0

	def feed(self, data):
		for (sample,) in struct.iter_unpack('<h', data):
			level = self.last_level
			high_byte = sample >> 8
			if self.LEVEL_THRESHOLD < high_byte < 70:
				level = 1
			elif 20 < high_byte < self.LEVEL_THRESHOLD:
				level = 0

			if level != self.last_level:
				if self.last_edge >= self.BITTIME_BOUND_LOWER:
					self.bits.append(0)
				else:
					if len(self.bits) > self.PACKET_MIN_BITS:
						yield from self._decode_bits()
					self.bits = []
				self.last_edge = 0

			if self.last_edge >= self.BITTIME_BOUND_UPPER:
				self.last_edge -= self.BITTIME
				self.bits.append(1)

			self.last_edge += 1
			self.last_level = level

	def _decode_bits(self):
		packet = False
		packet_bytes = []
		one_count = 0
		received_byte = 0
		received_bits = 0

		for index in range(17, len(self.bits)):
			bit = self.bits[index]
			if index > 17:
				bit ^= self.bits[index - 17]
			if index > 12:
				bit ^= self.bits[index - 12]

			if bit:
				one_count += 1
				received_byte = (received_byte >> 1) | 0x80
				received_bits += 1
				if received_bits == 8 and packet:
					packet_bytes.append(received_byte)
					received_bits = 0
			else:
				if one_count < 5:
					received_byte >>= 1
					received_bits += 1
					if received_bits == 8 and packet:
						packet_bytes.append(received_byte)
						received_bits = 0
				if one_count == 6:
					packet = not packet
					received_bits = 0
					if len(packet_bytes) == 41:
						yield packet_bytes
					packet_bytes = []
				one_count = 0


def decode_rtl_fm_packet(packet):
	"""Decode the fields exposed by the original rtl_fm compatibility decoder."""
	device_id = ((packet[0] & 0x0f) << 12) | (packet[1] << 4) | (packet[2] >> 4)
	power_current = ((packet[15] & 0x0f) << 12) | (packet[16] << 4) | (packet[17] >> 4)
	energy = ((packet[33] & 0x0f) << 12) | (packet[34] << 4) | (packet[35] >> 4)
	energy = (energy << 28) | (packet[12] << 20) | (packet[13] << 12) | (packet[14] << 4) | (packet[15] >> 4)
	return device_id, power_current, energy


def run_rtl_fm_loop(fd):
	packetizer = RtlFmPacketizer()
	while True:
		data = fd.read(BUFFSIZE)
		if not data:
			break
		for packet in packetizer.feed(data):
			device_id, power_current, energy = decode_rtl_fm_packet(packet)
			print('%d,%x,%d,%d' % (int(time.time()), device_id, power_current, energy), flush=True)


def run_loop(fd):
	
	packetizer = Packetizer()

	data = fd.read(BUFFSIZE)
	readlen = len(data)
	while readlen > 0:
		
		# packetizer
		for packet in packetizer.feed(data):
			packet.recover_clock()
			#print packet
		
		data = fd.read(BUFFSIZE)
		readlen = len(data)
	
	
def main():
	global verbose

	parser = OptionParser()

	parser.add_option("-f", dest="input", metavar="FILE",
			help="read baseband data from FILE")
	parser.add_option("-v", dest="verbose", action="store_true",
			help="enable verbose decoder debug output on stderr")
	parser.add_option("--rtl-fm", dest="rtl_fm", action="store_true",
			help="decode signed 16-bit output from rtl_fm -A fast")

	(options, args) = parser.parse_args()

	if options.input:
		fd = open(options.input, 'rb')
	else:
		fd = sys.stdin.buffer

	verbose = options.verbose

	if options.rtl_fm:
		run_rtl_fm_loop(fd)
	else:
		run_loop(fd)


if __name__ == "__main__":
	main()
