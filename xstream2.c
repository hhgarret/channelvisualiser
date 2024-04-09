/*
This should be a command line utility which demonstrates the functionality of libxdaq.

Its primary purpose is to be a coding example for using the libxdaq library.
It should be able to take cmd line args to demonstrate different functionality.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>

#include <time.h>

#include "xdaq.h"
#include <simplePipe.h>
//#include "xdaq_utils.h" // unpack_frame()

#define GPS_FMT "DATE: %04d-%02d-%02d\n" \
                "TIME: %f\n" \
                "SATS: %d\n" \
                "LAT:  %f\n" \
                "LON:  %f\n" \
                "ALT:  %f\n" \
                "POS:  %s\n" \
                "\n"

unsigned int dev_pid = 0; // 0xb1
unsigned int length_of_file = 0; // seconds

volatile int run = 1;

// signal handler
static void sig_handler(int sig)
{
	run = 0;
}

int main(int argc, char **argv)
{
	// check args
	if (argc != 6 && argc !=5 && argc !=7 && argc != 8) {
		fprintf(stderr, "Usage: %s --devicePID <device PID (hex): 0xXX> --uniqueID <unique ID (hex): 0xXX> [optional: --enableFaucet] [optional: <GPS/OBS> ] [optional: --human]\n", argv[0]);
		return 1;
	}
	unsigned int dev_pid = 0;
	unsigned int uniq_id = 0;
	unsigned int streamGPS = 0;
	unsigned int streamOBS = 0;
	unsigned int humanFlag = 0;
	//simplePipe<unsigned,1> xstreamControl("/tmp/xstreamControl", O_RDONLY);
	simplePipe<unsigned,1>* xstreamControl;
	unsigned message[1];
	unsigned qFaucet = 0;
	unsigned enableFaucet = 0;
	for(int arg = 0; arg < argc; ++arg) {
		if(strcmp(argv[arg], "--devicePID") == 0) {
			// set device pid
			if (!sscanf(argv[arg + 1], "0x%02X", &dev_pid)) {
				if (!sscanf(argv[arg + 1], "0x%02x", &dev_pid)) {
					fprintf(stderr, "%s: failed to parse device pid argument: '%s'\n", argv[0], argv[1]);
					return 1;
				}
			}
		} else if(strcmp(argv[arg], "--uniqueID") == 0) {
			// set unique id
			if (!sscanf(argv[arg + 1], "0x%02X", &uniq_id)) {
				if (!sscanf(argv[arg + 1], "0x%02x", &uniq_id)) {
					fprintf(stderr, "%s: failed to parse unique id argument: '%s'\n", argv[0], argv[2]);
					return 1;
				}
			}
		} else if(strcmp(argv[arg], "GPS") == 0) {
			streamGPS = 1;
		} else if(strcmp(argv[arg], "OBS") == 0) {
			streamOBS = 1;
		} else if(strcmp(argv[arg], "--enableFaucet") == 0) {
			enableFaucet = 1;
			xstreamControl = new simplePipe<unsigned,1>("/tmp/xstreamControl", O_RDONLY);
		}else if(strcmp(argv[arg], "--human") == 0){
			humanFlag = 1;
		}
	}
	unsigned streamBOTH = 0;
	if(streamGPS == 0 && streamOBS == 0) {
		streamGPS = 0;
		streamOBS = 0;
		streamBOTH = 1;
	}

	// attach signal handler
	struct sigaction sia;
	sia.sa_handler = sig_handler;
#ifdef DEBUG
	if (sigaction(SIGINT, &sia, NULL) < 0)
		fprintf(stderr, "WARN: could not attach signal handler.\n");
#endif
	// init libxdaq
	xdaq_config_t conf;
	memset(&conf, 0, sizeof(xdaq_config_t));
	conf.pid = dev_pid;
	conf.n_transfers = 16; // more transfers -> more bandwidth (use a lot for high-n)
	conf.n_packets = 10;
	unsigned packetSize = 512;

	int err = xdaq_init(&conf);
	if (err != 0) {
#ifdef DEBUG
		fprintf(stderr, "Failed to initialize: %d\n", err);
#endif
		return -1;
	}
#ifdef DEBUG
	fprintf(stderr, "initialized xdaq\n");
#endif

	xdaq_start(&conf);
#ifdef DEBUG
	fprintf(stderr, "started xdaq\n");
#endif

	struct gps_data gps;
	bool firstHeader = false;
	while (1) {
		// blocking read call... reads from fifo
		//struct data_packet *packet = xdaq_read(&conf);

		char *packets = xdaq_read(&conf);
		if (packets == NULL) {
#ifdef DEBUG
			fprintf(stderr, "xrecord: packets == NULL\n");
#endif
			continue;
		}

		// TODO: user might want to check status flags (overflow, etc)
#if 1
		// TODO: process the header
		struct data_header *headers = extract_headers(packets, conf.n_packets);

		uint8_t n_chan = headers[0].n_chan;
		uint8_t n_frame = headers[0].n_frame;
		uint8_t prod_id = headers[0].prod_id;
		uint32_t first_frame_index = headers[0].frm_idx;
		uint8_t extra_len = 0;

		if(!firstHeader && !humanFlag){
			char n_chanc = (char) n_chan;
			char* arr = &n_chanc;
			fwrite(arr, sizeof(char), 1, stdout);
			//printf("%x\n", n_chanc);
			if(n_chanc == 0x18)
				firstHeader = 1;
		}

/*
		printf("n_chan = %d\n", headers[0].n_chan);
		printf("n_frame = %d\n", headers[0].n_frame);
		printf("prod_id = 0x%02X\n", headers[0].prod_id);
		printf("frm_idx = %d\n", headers[0].frm_idx);
		printf("extra_len= %d\n", headers[0].extra_len);
*/

		// Check other packets for GPS data
		for (int p = 0; p < conf.n_packets; ++p) {
			extra_len = headers[p].extra_len;
			if(extra_len > 0) {
#ifdef DEBUG
				fprintf(stderr, "Packet number: %d\n", p);
#endif
				memcpy(&gps, (struct gps_data*) headers[p].extra_data, sizeof(struct gps_data));
				break;
			}
		}


		uint16_t s_rate = 0;
		if (prod_id == 0xb1 || prod_id == 0xb3) {
			s_rate = 48000;
		} else if (prod_id == 0xb2) {
			s_rate = 500;
		}

		static uint32_t expected_frame_index = 0;

		if (expected_frame_index != first_frame_index) {
#ifdef DEBUG
			fprintf(stderr, "expected %u, got %u\n", expected_frame_index, first_frame_index);
#endif
		}

		expected_frame_index = (first_frame_index + n_frame * conf.n_packets) % s_rate;
#endif
		union converter{
			char c[4];
			int32_t i;
		};
		if(enableFaucet) {
			int bytes = xstreamControl->pipeIn(message);
			if(bytes > 0) qFaucet = message[0];
		}
		if(streamBOTH && (!enableFaucet || qFaucet) && humanFlag) {
			float timeStamp = gps.utc_time;
			float latitude = gps.lat;
			float longitude = gps.lon;
			float altitude = gps.alt;

			remove_headers(packets, conf.n_packets);
			for (int p = 0; p < conf.n_packets; ++p) { //human both
				int32_t *samples = (int32_t*) &packets[p * packetSize];
				for(int f = 0; f < n_frame; f++) {
					printf("%f\t%f\t%f\t%f\t", timeStamp, latitude, longitude, altitude);
					for(int c = 0; c < n_chan; ++c) {
						//printf("%d\t", samples[c + f*n_chan]);
						if(c < n_chan - 1)
							printf("%lf\t", 1.0 * samples[c + f*n_chan]/INT_MAX);
						else
							printf("%lf\n", 1.0 * samples[c + f*n_chan]/INT_MAX);
					}
				}
			} //binary both
		}else if(streamBOTH && (!enableFaucet || qFaucet) && !humanFlag) {
			float timeStamp = gps.utc_time;
			float latitude = gps.lat;
			float longitude = gps.lon;
			float altitude = gps.alt;

			remove_headers(packets, conf.n_packets);
			union converter conv;
			for (int p = 0; p < conf.n_packets; ++p) {
				int32_t *samples = (int32_t*) &packets[p * packetSize];
				for(int f = 0; f < n_frame; f++) {
					//printf("%f\t%f\t%f\t%f\t", timeStamp, latitude, longitude, altitude);
					fwrite(&timeStamp, sizeof(float), 1, stdout);
					fwrite(&latitude, sizeof(float), 1, stdout);
					fwrite(&longitude, sizeof(float), 1, stdout);
					fwrite(&altitude, sizeof(float), 1, stdout);
					int i = 0;
					int length = n_chan;
					double *convsamples = (double*)malloc(length * sizeof(double));
					for(int c = 0; c < n_chan; ++c) {
					convsamples[i] = 1.0*samples[c+f*n_chan]/INT_MAX;
					i++;
					}
					
				fwrite(convsamples, sizeof(double), length, stdout);
				}
			}
		}
		else if (extra_len > 0 && streamGPS && (!enableFaucet || qFaucet) && humanFlag) { //human readable GPS
			char gps_output[420];
			sprintf(gps_output, GPS_FMT,
					gps.utc_year, gps.utc_month, gps.utc_day, gps.utc_time,
					gps.num_sv,
					gps.lat, gps.lon, gps.alt,
					gps.pos_mode
				);
			printf("%s\n", gps_output);
		}else if (extra_len > 0 && streamGPS && (!enableFaucet || qFaucet) && !humanFlag) { //binary GPS
			char gps_output[420];
			sprintf(gps_output, GPS_FMT,
					gps.utc_year, gps.utc_month, gps.utc_day, gps.utc_time,
					gps.num_sv,
					gps.lat, gps.lon, gps.alt,
					gps.pos_mode
				);
			fwrite(gps_output, sizeof(char), 420, stdout);
		} //human readable OBS
		else if(streamOBS && (!enableFaucet || qFaucet) && humanFlag) {
			remove_headers(packets, conf.n_packets);
			for (int p = 0; p < conf.n_packets; ++p) {
				int32_t *samples = (int32_t*) &packets[p * packetSize];
				for(int f = 0; f < n_frame; f++) {
					for(int c = 0; c < n_chan; ++c) {
						//printf("%d\t", samples[c + f*n_chan]);
						if(c < n_chan - 1)
							printf("%lf\t", 1.0 * samples[c + f*n_chan]/INT_MAX);
						else
							printf("%lf\n", 1.0 * samples[c + f*n_chan]/INT_MAX);
					}
				}
			}
		} //binary OBS
		else if(streamOBS && (!enableFaucet || qFaucet) && !humanFlag){
			remove_headers(packets, conf.n_packets);
			union converter conv;
			for (int p = 0; p < conf.n_packets; ++p) {
				int32_t *samples = (int32_t*) &packets[p * packetSize];
				int length = n_chan;
				double *convsamples = (double*)malloc(length * sizeof(double));
				
				for(int f = 0; f < n_frame; f++){
				int i = 0;
					for(int c = 0; c < n_chan; ++c){
					convsamples[i] = 1.0*samples[c+f*n_chan]/INT_MAX;
					i++;
					}
				fwrite(convsamples, sizeof(double), length, stdout);
				}
			}
		}
		// user must free packets and headers memory
		free(packets);
		free(headers);
	}
#ifdef DEBUG
	fprintf(stderr,"stopping xdaq\n");
#endif
	xdaq_stop(&conf);
#ifdef DEBUG
	fprintf(stderr,"stopped xdaq\n");
#endif

	//fclose(fp_out);
	xdaq_deinit(&conf);
	if(enableFaucet == 1)
			delete(xstreamControl);

#ifdef DEBUG
	fprintf(stderr,"Bye\n");
#endif
	return 0;
}
