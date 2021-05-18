import re
import argparse
import subprocess
import os
import logging
import json

from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily
from prometheus_client import make_wsgi_app
from wsgiref.simple_server import make_server, WSGIRequestHandler


class SmartctlCollector(object):
    def __init__(self, smartdconf_path):
        self.paths = []
        # Use the paths defined in smartd.conf
        with open(smartdconf_path, 'r') as smartdconf:
            for line in smartdconf:
                m = re.match(r"^(\/dev\/.*?)\s", line)
                if m:
                    self.paths.append(m.group(1))
        logging.debug('Extrated these paths from smartd.conf: {}'.format(self.paths))

    def collect(self):
        logging.debug('Start of collection cycle')
        labels_disk = ['path', 'jbod_name', 'slot_number',
                       'serial_number', 'vendor', 'product',
                       'model_name', 'revision', 'scsi_version',
                       'user_capacity_bytes', 'rotation_rate']

        counter_minutes = CounterMetricFamily('smartctl_minutes',
            'How long was the disk powered since it was built',
             labels=labels_disk)
        gauge_temperature = GaugeMetricFamily('smartctl_temperature',
            'The disk temperature', labels=labels_disk)
        gauge_smart_status = GaugeMetricFamily('smartctl_smart_status',
            'Smart status passed', labels=labels_disk)
        counter_grown_defect_list = CounterMetricFamily(
            'smartctl_grown_defect_list',
            'The number of defects detected on the disk', labels=labels_disk)
        counter_read_errors_corrected_by_eccfast = CounterMetricFamily(
            'smartctl_read_errors_corrected_by_eccfast',
            'Read error corrected by eccfast', labels=labels_disk)
        counter_write_errors_corrected_by_eccfast = CounterMetricFamily(
            'smartctl_write_errors_corrected_by_eccfast',
            'Write error corrected by eccfast', labels=labels_disk)
        counter_read_errors_corrected_by_eccdelayed = CounterMetricFamily(
            'smartctl_read_errors_corrected_by_eccdelayed',
            'Read error corrected by eccdelayed', labels=labels_disk)
        counter_write_errors_corrected_by_eccdelayed = CounterMetricFamily(
            'smartctl_write_errors_corrected_by_eccdelayed',
            'Write error corrected by eccdelayed', labels=labels_disk)
        counter_read_errors_corrected_by_rereads_rewrites = CounterMetricFamily(
            'smartctl_read_errors_corrected_by_rereads_rewrites',
            'Read error corrected by rereads rewrites', labels=labels_disk)
        counter_write_errors_corrected_by_rereads_rewrites = CounterMetricFamily(
            'smartctl_write_errors_corrected_by_rereads_rewrites',
            'Write error corrected by rereads rewrites', labels=labels_disk)
        counter_read_total_errors_corrected = CounterMetricFamily(
            'smartctl_read_total_errors_corrected',
            'Read total error corrected', labels=labels_disk)
        counter_write_total_errors_corrected = CounterMetricFamily(
            'smartctl_write_total_errors_corrected',
            'Write total error corrected', labels=labels_disk)
        counter_read_correction_algorithm_invocations = CounterMetricFamily(
            'smartctl_read_correction_algorithm_invocations',
            'Read correction algorithm invocations', labels=labels_disk)
        counter_write_correction_algorithm_invocations = CounterMetricFamily(
            'smartctl_write_correction_algorithm_invocations',
            'Write correction algorithm invocations', labels=labels_disk)
        counter_read_gigabytes = CounterMetricFamily(
            'smartctl_read_gigabytes',
            'Number of gigabytes read', labels=labels_disk)
        counter_write_gigabytes = CounterMetricFamily(
            'smartctl_write_gigabytes',
            'Number of gigabytes write', labels=labels_disk)
        gauge_failed_short_self_test = GaugeMetricFamily('smartctl_failed_short_self_test',
            'Number of failed short self-test', labels=labels_disk)
        gauge_failed_long_self_test = GaugeMetricFamily('smartctl_failed_long_self_test',
            'Number of failed long self-test', labels=labels_disk)
        counter_non_medium_errors = CounterMetricFamily(
            'smartctl_non_medium_errors',
            'Non-medium error count', labels=labels_disk)
        gauge_endurance_indicator = GaugeMetricFamily('smartctl_endurance_indicator',
            'SSD endurance indicator, in percent', labels=labels_disk)

        for path in self.paths:
            if os.path.exists(path) is False:
                logging.warning('Disk {} is not present'.format(path))
                continue

            # Trying to match our jbod/slot naming format
            m = re.match(r'.*single_(.*)-bay(\d+)', path)
            if m:
                jbod_name = m.group(1)
                slot_number = m.group(2)
            else:
                jbod_name = 'N/A'
                slot_number = 'N/A'

            smartctl_args = ['/usr/sbin/smartctl', '--xall', '--json=o', path]
            logging.debug('Running {}'.format(smartctl_args))
            process = subprocess.Popen(smartctl_args,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            process_stdout, process_stderr = process.communicate()
            smartctl_stdout = process_stdout.decode("utf-8")

            j = json.loads(smartctl_stdout)

            logging.debug(j)

            labels = [path, jbod_name, slot_number,
                      j['serial_number'], j['vendor'], j['product'],
                      j['model_name'], j['revision'], j['scsi_version'],
                      str(j['user_capacity']['bytes']),
                      str(j['rotation_rate'])]
            minutes = j['power_on_time']['hours'] * 60 + j['power_on_time']['minutes']
            counter_minutes.add_metric(labels, minutes)
            gauge_temperature.add_metric(labels, str(j['temperature']['current']))
            if j['smart_status']['passed']:
                gauge_smart_status.add_metric(labels, "1")
            else:
                gauge_smart_status.add_metric(labels, "0")
            try:
                # Does not seem to always exist on SSDs
                counter_grown_defect_list.add_metric(labels, str(j['scsi_grown_defect_list']))
            except KeyError:
                pass
            counter_read_errors_corrected_by_eccfast.add_metric(labels,
                str(j['scsi_error_counter_log']['read']['errors_corrected_by_eccfast']))
            counter_write_errors_corrected_by_eccfast.add_metric(labels,
                str(j['scsi_error_counter_log']['write']['errors_corrected_by_eccfast']))
            counter_read_errors_corrected_by_eccdelayed.add_metric(labels,
                str(j['scsi_error_counter_log']['read']['errors_corrected_by_eccdelayed']))
            counter_write_errors_corrected_by_eccdelayed.add_metric(labels,
                str(j['scsi_error_counter_log']['write']['errors_corrected_by_eccdelayed']))
            counter_read_errors_corrected_by_rereads_rewrites.add_metric(labels,
                str(j['scsi_error_counter_log']['read']['errors_corrected_by_rereads_rewrites']))
            counter_write_errors_corrected_by_rereads_rewrites.add_metric(labels,
                str(j['scsi_error_counter_log']['write']['errors_corrected_by_rereads_rewrites']))
            counter_read_total_errors_corrected.add_metric(labels,
                str(j['scsi_error_counter_log']['read']['total_errors_corrected']))
            counter_write_total_errors_corrected.add_metric(labels,
                str(j['scsi_error_counter_log']['write']['total_errors_corrected']))
            counter_read_correction_algorithm_invocations.add_metric(labels,
                str(j['scsi_error_counter_log']['read']['correction_algorithm_invocations']))
            counter_write_correction_algorithm_invocations.add_metric(labels,
                str(j['scsi_error_counter_log']['write']['correction_algorithm_invocations']))
            counter_read_gigabytes.add_metric(labels,
                str(j['scsi_error_counter_log']['read']['gigabytes_processed']))
            counter_write_gigabytes.add_metric(labels,
                str(j['scsi_error_counter_log']['write']['gigabytes_processed']))

            # counting the number of failed self-test
            failed_short = 0
            failed_long = 0
            for line in j['smartctl']['output']:
                m = re.match(r'.*Background (long|short)\s+(Completed|Self test in progress|Failed in segment).*', line)
                if m:
                    if(str(m.group(2)) == 'Failed in segment'):
                        length = str(m.group(1))
                        if length == 'short':
                            failed_short += 1
                        elif length == 'long':
                            failed_long += 1
                m_medium = re.match(r'Non-medium error count:\s+(\d+)', line)
                if m_medium:
                    counter_non_medium_errors.add_metric(labels, str(m_medium.group(1)))
            gauge_failed_short_self_test.add_metric(labels, str(failed_short))
            gauge_failed_long_self_test.add_metric(labels, str(failed_long))

            try:
                gauge_endurance_indicator.add_metric(labels,
                    str(j['scsi_percentage_used_endurance_indicator']))
            except KeyError:
                pass

        yield counter_minutes
        yield gauge_temperature
        yield gauge_smart_status
        yield counter_grown_defect_list
        yield counter_read_errors_corrected_by_eccfast
        yield counter_write_errors_corrected_by_eccfast
        yield counter_read_errors_corrected_by_eccdelayed
        yield counter_write_errors_corrected_by_eccdelayed
        yield counter_read_errors_corrected_by_rereads_rewrites
        yield counter_write_errors_corrected_by_rereads_rewrites
        yield counter_read_total_errors_corrected
        yield counter_write_total_errors_corrected
        yield counter_read_correction_algorithm_invocations
        yield counter_write_correction_algorithm_invocations
        yield counter_read_gigabytes
        yield counter_write_gigabytes
        yield gauge_failed_short_self_test
        yield gauge_failed_long_self_test
        yield counter_non_medium_errors
        yield gauge_endurance_indicator
        logging.debug('End of collection cycle')


class NoLoggingWSGIRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Prometheus collector for smartctl')
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Collector http port, default is 8080')
    parser.add_argument(
        '--smartdconf',
        type=str,
        default='/etc/smartmontools/smartd.conf',
        help='Path to smartd.conf'
    )
    parser.add_argument("--verbose", help="increase output verbosity",
                        action="store_true")

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
    app = make_wsgi_app(SmartctlCollector(args.smartdconf))
    httpd = make_server('', args.port, app,
                        handler_class=NoLoggingWSGIRequestHandler)
    httpd.serve_forever()
