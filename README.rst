Software receiver for EnergyCount 3000
======================================

This module allows you to receive and decode radio transmissions from
EnergyCount 3000 energy loggers using a RTL-SDR supported radio receiver and
the GNU Radio software defined radio framework.

EnergyCount 3000 transmitters plug between a device and an AC power outlet
and monitor electrical energy usage. They transmit a packet with a status
update every 5 seconds on the 868 MHz SRD band. Reported values include
id of the device, current and maximum seen electrical power, total energy
used and device on time.


Module content
--------------

The module exports a class that represents the radio receiver. You provide
it with a callback function that is called each time a new status update is
received::

    def callback(state):
        print(state)

    my_ec3k = ec3k.EnergyCount3K(callback=callback)

    my_ec3k.start()
    while not want_stop:
        time.sleep(2)
        print("Noise level: %.1f dB" % my_ec3k.noise_level)

    my_ec3k.stop()

The command-line receiver writes a tab-separated record for each status update::

    timestamp  id  time_total  time_on  energy  power_current  power_max  reset_counter

``time_total`` is a transmitter firmware counter and can remain at its maximum
value. Use receive timestamps or ``time_on`` for elapsed-time calculations.

You can also get the last received state by calling the ``get`` method on
the EnergyCount3K object. See docstrings for details.

Also included is an example command-line client ``ec3k_recv`` that prints
received packets to standard output.


Requirements
------------

You need Python 3.10 or newer, GNU Radio 3.10 or newer, rtl-sdr, SoapySDR,
and the SoapyRTLSDR driver module. The optional ``--source osmosdr`` backend
also requires gr-osmosdr with RTL-SDR support.

For baseband decoding a pure Python implementation is included in this
package (``capture.py``) and should work out of the box.

Installation
------------

Install the system SDR dependencies and this package through your Linux
distribution's package manager. The project deliberately has no Python
runtime dependencies managed by pip.

Run the offline regression suite with::

    $ python3 -m pytest

To try it out, run the example command-line client::

    $ ec3k_recv

The GNU Radio receiver defaults to 868.225 MHz. Set ``--frequency`` when
calibrating another receiver or channel.

On the current RTL-SDR, a 40-second live sweep produced 26 CRC-valid records
at 868.225 MHz, compared with 15 at the previous 868.260 MHz default. Tune
``--ppm`` and repeat the sweep when using a different dongle or antenna.

For troubleshooting or compatibility with the ``rtl_fm`` demodulator, the
included capture utility can decode its signed 16-bit output::

    $ rtl_fm -f 868402000 -s 200000 -A fast - | capture.py --rtl-fm

This compatibility mode writes ``timestamp,id,power_x10,energy`` CSV records.
The main receiver can use the same proven front end while retaining the full
EC3K state decoder and TSV or JSON Lines output::

    $ ec3k_recv --rtl-fm

``ec3k_recv`` uses GNU Radio's SoapySDR source by default. The optional
``--source osmosdr`` backend is available for differential testing against
the historical gr-osmosdr receiver path.

Please note that the receiver needs some time to adapt to the signal and noise
level in your environment. It might take a few minutes before ``ec3k_recv``
prints out any decoded packets.


Feedback
--------

Please send patches or bug reports to <tomaz.solc@tablix.org>


Source
------

You can get a local copy of the development repository with::

    git clone git://github.com/avian2/ec3k.git


License
-------

ec3k, software receiver for EnergyCount 3000

Copyright (C) 2015  Tomaz Solc <tomaz.solc@tablix.org>

Copyright (C) 2012  Gasper Zejn

Protocol reverse engineering: http://forum.jeelabs.net/comment/4020

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

..
    vim: set filetype=rst:
