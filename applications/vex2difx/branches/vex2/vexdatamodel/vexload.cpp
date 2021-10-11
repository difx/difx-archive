/***************************************************************************
 *   Copyright (C) 2009-2021 by Walter Brisken                             *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
 ***************************************************************************/
/*===========================================================================
 * SVN properties (DO NOT CHANGE)
 *
 * $Id$
 * $HeadURL$
 * $LastChangedRevision$
 * $Author$
 * $LastChangedDate$
 *
 *==========================================================================*/

#include <fstream>
#include <cstring>
#include <cstdlib>

#include <cstring>
#include <cctype>
#include <cstdio>
#include <algorithm>
#include <unistd.h>
#include "vex_utility.h"
#include "vex_data.h"
#include "../vex/vex.h"
#include "../vex/vex_parse.h"

// maximum number of defined IFs
#define MAX_IF 64

using namespace std;

class BitAssignments
{
public:
	std::vector<int> sign;
	std::vector<int> mag;
};

int reorderBitAssignments(std::map<std::string,BitAssignments> &bitAssignements, int startSlotNumber)
{
	const int MaxSlotNumber = 66;
	int order[MaxSlotNumber+1];

	for(int i = 0; i <= MaxSlotNumber; ++i)
	{
		order[i] = -2;
	}

	for(std::map<std::string,BitAssignments>::iterator it = bitAssignements.begin(); it != bitAssignements.end(); ++it)
	{
		const BitAssignments &T = it->second;

		for(std::vector<int>::const_iterator b = T.sign.begin(); b != T.sign.end(); ++b)
		{
			if(*b < 0 || *b > MaxSlotNumber)
			{
				cerr << "Error: sign assignment " << *b << " for channel " << it->first << " is out of range (0.." << MaxSlotNumber << ").  Must quit." << endl;

				exit(EXIT_FAILURE);
			}
			if(order[*b] != -2)
			{
				cerr << "Error: sign assignment " << *b << " for channel " << it->first << " is repeated.  Must quit." << endl;

				exit(EXIT_FAILURE);
			}
			order[*b] = -1;
		}

		for(std::vector<int>::const_iterator b = T.mag.begin(); b != T.mag.end(); ++b)
		{
			if(*b < 0 || *b > MaxSlotNumber)
			{
				cerr << "Error: mag assignment " << *b << " for channel " << it->first << " is out of range (0.." << MaxSlotNumber << ").  Must quit." << endl;

				exit(EXIT_FAILURE);
			}
			if(order[*b] != -2)
			{
				cerr << "Error: mag assignment " << *b << " for channel " << it->first << " is repeated.  Must quit." << endl;

				exit(EXIT_FAILURE);
			}
			order[*b] = -1;
		}
	}

	int newSlotNumber = startSlotNumber;
	for(int i = 0; i < 67; ++i)
	{
		if(order[i] == 1)
		{
			order[i] = newSlotNumber;
			++newSlotNumber;
		}
	}

	for(std::map<std::string,BitAssignments>::iterator it = bitAssignements.begin(); it != bitAssignements.end(); ++it)
	{
		BitAssignments &T = it->second;

		for(std::vector<int>::iterator b = T.sign.begin(); b != T.sign.end(); ++b)
		{
			*b = order[*b];
		}

		for(std::vector<int>::iterator b = T.mag.begin(); b != T.mag.end(); ++b)
		{
			*b = order[*b];
		}
	}

	return 0;
}

static void fixOhs(std::string &str)
{
	unsigned int i;

	// The format of Mark5/6 disk packs is name&number where name
	// is a four character string for Mark5 and a 3 character stream for
	// Mark6.  The delimiter for Mark5 is a + or a - while the Mark5 uses
	// the % sign.  This method fixes any zeroes that happen to be in the
	// name section by turning them to capital O's.

	for(i = 0; i < str.length(); ++i)
	{
		if(str[i] == '-' || str[i] == '+' || str[i] == '%')
		{
			break;
		}
		if(str[i] == '0')
		{
			str[i] = 'O';
		}
	}
}

static int getRecordChannelFromTracks(const std::string &antName, const std::string &chanName, const std::map<std::string,BitAssignments> &ch2tracks, const VexStream &stream, unsigned int n)
{
	if(stream.formatHasFanout())
	{
		int delta, track;
		std::map<std::string,BitAssignments>::const_iterator it = ch2tracks.find(chanName);

		if(it == ch2tracks.end())
		{
			return -1;
		}

		const BitAssignments &T = it->second;
		delta = 2*(T.sign.size() + T.mag.size());
		track = T.sign[0];

		if(track < 34)
		{
			if(track % 2 == 0) 
			{
				return (track-2)/delta;
			}
			else
			{
				return (track+29)/delta;
			}
		}
		else
		{
			if(track % 2 == 0)
			{
				return (track+30)/delta;
			}
			else
			{
				return (track+61)/delta;
			}
		}
	}
	else if(stream.format == VexStream::FormatMark5B || stream.format == VexStream::FormatKVN5B) 
	{
		int delta, track;
		std::map<std::string,BitAssignments>::const_iterator it = ch2tracks.find(chanName);

		if(it == ch2tracks.end())
		{
			return -1;
		}

		const BitAssignments &T = it->second;

		if(T.sign.empty())
		{
			cerr << "Note: antenna " << antName << " has Mark5B format but no tracks defined in the vex file." << endl;

			return -1;
		}

		delta = T.sign.size() + T.mag.size();
		track = T.sign[0];

		return (track-2)/delta;
	}
	else if(stream.isLBAFormat())
	{
		int delta, track;
		std::map<std::string,BitAssignments>::const_iterator it = ch2tracks.find(chanName);

		if(it == ch2tracks.end())
		{
			return -1;
		}

		const BitAssignments &T = it->second;
		delta = T.sign.size() + T.mag.size();
		track = T.sign[0];

                return track/delta;
	}
	else if(stream.format == VexStream::FormatS2)
	{
		return n;
	}
	else if(stream.isVDIFFormat())
	{
		return n;
	}
	else if(stream.format == VexStream::FormatNone)
	{
		return 0;
	}
	else
	{
		std::cerr << "Error: Antenna=" << antName << " format \"" << VexStream::DataFormatNames[stream.format] << "\" is not yet supported" << std::endl;
		std::cerr << "Contact developer." << std::endl;

		exit(EXIT_FAILURE);
	}

	return -1;
}

static int getRecordChannelFromBitstreams(const std::string &antName, const std::string &chanName, const std::map<std::string,BitAssignments> &ch2bitstreams, const VexStream &stream, unsigned int n)
{
	int delta, track;
	std::map<std::string,BitAssignments>::const_iterator it = ch2bitstreams.find(chanName);

	if(it == ch2bitstreams.end())
	{
		return -1;
	}

	const BitAssignments &T = it->second;

	if(T.sign.empty())
	{
		cerr << "Note: antenna " << antName << " has Mark5B format but no tracks defined in the vex file." << endl;

		return -1;
	}

	delta = T.sign.size() + T.mag.size();
	track = T.sign[0];

	return track/delta;
}

int DOYtoMJD(int year, int doy)
{
	return doy-678576+365*(year-1)+(year-1)/4-(year-1)/100+(year-1)/400;
}

double vexDate(char *value)
{
	double mjd;
	int n = 0;
	
	for(int i = 0; value[i]; ++i)
	{
		if(isalpha(value[i]))
		{
			++n;
		}
	}

	if(n == 0)
	{
		// assume this is mjd
		mjd = atof(value);
		if(sscanf(value, "%lf", &mjd) != 1)
		{
			std::cerr << "Error: vex date is not in usable format: " << value << std::endl;

			exit(EXIT_FAILURE);
		}
	}
	else
	{
		int i;
		int start = 0;
		double years = 0.0;
		double days = 0.0;
		double hours = 0.0;
		double minutes = 0.0;
		double seconds = 0.0;
		double x;

		for(i = 0; value[i]; ++i)
		{
			if(isalpha(value[i]))
			{
				if(sscanf(value+start, "%lf", &x) != 1)
				{
					std::cerr << "Error: vex date is not in usable format: " << value << std::endl;

					exit(EXIT_FAILURE);
				}
				switch(value[i])
				{
				case 'y':
					years = x;
					break;
				case 'd':
					days = x;
					break;
				case 'h':
					hours = x;
					break;
				case 'm':
					minutes = x;
					break;
				case 's':
					seconds = x;
					break;
				default:
					std::cerr << "Error: vex date is not in usable format: " << value << std::endl;

					exit(EXIT_FAILURE);
				}

				start = i+1;
			}
		}

		if(start != i)
		{
			std::cerr << "Error: trailing characters in vex date: " << value << std::endl;

			exit(EXIT_FAILURE);
		}

		mjd = DOYtoMJD( static_cast<int>(floor(years+0.1)), static_cast<int>(floor(days+0.1)) ) + hours/24.0 + minutes/1440.0 + seconds/86400.0;
	}

	return mjd;
}

static int getAntennas(VexData *V, Vex *v)
{
	struct dvalue *r;
	llist *block;
	int nWarn = 0;

	block = find_block(B_CLOCK, v);

	for(char *stn = get_station_def(v); stn; stn=get_station_def_next())
	{
		struct site_position *p;
		struct axis_type *q;
		VexAntenna *A;

		std::string antName(stn);
		Upper(antName);

		A = V->newAntenna();
		A->name = stn;
		A->defName = stn;
		Upper(A->name);

		p = (struct site_position *)get_station_lowl(stn, T_SITE_POSITION, B_SITE, v);
		if(p == 0)
		{
			std::cerr << "Warning: cannot find site position for antenna " << antName << " in the vex file." << std::endl;
			++nWarn;
		}
		else
		{
			fvex_double(&(p->x->value), &(p->x->units), &A->x);
			fvex_double(&(p->y->value), &(p->y->units), &A->y);
			fvex_double(&(p->z->value), &(p->z->units), &A->z);
		}

		p = (struct site_position *)get_station_lowl(stn, T_SITE_VELOCITY, B_SITE, v);
		if(p)
		{
			fvex_double(&(p->x->value), &(p->x->units), &A->dx);
			fvex_double(&(p->y->value), &(p->y->units), &A->dy);
			fvex_double(&(p->z->value), &(p->z->units), &A->dz);
		}
		else
		{
			A->dx = A->dy = A->dz = 0.0;
		}

		q = (struct axis_type *)get_station_lowl(stn, T_AXIS_TYPE, B_ANTENNA, v);
		if(q == 0)
		{
			std::cerr << "Warning: cannot find axis type for antenna " << antName << " in the vex file." << std::endl;
			++nWarn;
		}
		else
		{
			A->axisType = std::string(q->axis1) + std::string(q->axis2);
			if(A->axisType.compare("hadec") == 0)
			{
				A->axisType = "equa";
			}
		}

		r = (struct dvalue *)get_station_lowl(stn, T_SITE_POSITION_EPOCH, B_SITE, v);
		if(r)
		{
			char *value;
			char *units;
			int name;
			int link;
			vex_field(T_SITE_POSITION_EPOCH, (void *)r, 1, &link, &name, &value, &units);

			A->posEpoch = vexDate(value);
		}
		else
		{
			A->posEpoch = 0.0;
		}

		r = (struct dvalue *)get_station_lowl(stn, T_AXIS_OFFSET, B_ANTENNA, v);
		if(r == 0)
		{
			std::cerr << "Warning: cannot find axis offset for antenna " << antName << " in the vex file." << std::endl;
		}
		else
		{
			fvex_double(&(r->value), &(r->units), &A->axisOffset);
		}

		for(void *c = get_station_lowl(stn, T_CLOCK_EARLY, B_CLOCK, v); c; c = get_station_lowl_next())
		{
			char *value;
			char *units;
			int name;
			int link;
			double mjd;

			vex_field(T_CLOCK_EARLY, c, 1, &link, &name, &value, &units);
			if(value)
			{
				mjd = vexDate(value);
			}
			else
			{
				mjd = 0.0;
			}
			A->clocks.push_back(VexClock());
			VexClock &clock = A->clocks.back();
			clock.mjdStart = mjd;

			vex_field(T_CLOCK_EARLY, c, 2, &link, &name, &value, &units);
			if(value && units)
			{
				fvex_double(&value, &units, &clock.offset);
			}

			vex_field(T_CLOCK_EARLY, c, 3, &link, &name, &value, &units);
			if(value)
			{
				clock.offset_epoch = vexDate(value);
				vex_field(T_CLOCK_EARLY, c, 4, &link, &name, &value, &units);
				if(value)
				{
					if(units)
					{
						fvex_double(&value, &units, &clock.rate);
					}
					else
					{
						clock.rate = atof(value);
					}
				}
			}
			clock.flipSign();
		}

		// As a last resort, look for unlinked clock blocks
#warning: "FIXME: note: the following should eventually be removed once proper linking in vex files is in place"
		if(A->clocks.empty() && block)
		{
			Llist *defs;
			
			defs = ((struct block *)block->ptr)->items;
			if(defs)
			{
				defs = find_def(defs, stn);
			}
			if(defs)
			{
				for(Llist *lowls = find_lowl(((Def *)((Lowl *)defs->ptr)->item)->refs, T_CLOCK_EARLY); lowls; lowls = lowls->next)
				{
					Clock_early *C;
					
					if(((Lowl *)lowls->ptr)->statement != T_CLOCK_EARLY)
					{
						continue;
					}

					C = (Clock_early *)(((Lowl *)lowls->ptr)->item);
					if(C)
					{
						double mjd;
						
						if(C->start)
						{
							mjd = vexDate(C->start);
						}
						else
						{
							mjd = 0.0;
						}
						A->clocks.push_back(VexClock());
						VexClock &clock = A->clocks.back();
						clock.mjdStart = mjd;
						if(C->offset)
						{
							fvex_double(&(C->offset->value), &(C->offset->units), &clock.offset);
						}
						if(C->rate && C->origin) 
						{
							if(C->rate->units)
							{
								fvex_double(&(C->rate->value), &(C->rate->units), &clock.rate);
							}
							else
							{
								clock.rate = atof(C->rate->value);
							}
							clock.offset_epoch = vexDate(C->origin);
						}
						
						// vex has the opposite sign convention, so swap
						clock.flipSign();
					}
				}
			}
		}
	}

	return nWarn;
}

static int getSources(VexData *V, Vex *v)
{
	int nWarn = 0;
	
	for(char *src = get_source_def(v); src; src=get_source_def_next())
	{
		VexSource *S;
		char *p;

		S = V->newSource();
		S->defName = src;
		if(strlen(src) > VexSource::MAX_SRCNAME_LENGTH)
		{
			std::cerr << "Source name " << src << " is longer than " << VexSource::MAX_SRCNAME_LENGTH << "  characters!" << std::endl;
			++nWarn;
		}

		for(p = (char *)get_source_lowl(src, T_SOURCE_NAME, v); p; p = (char *)get_source_lowl_next())
		{
			S->sourceNames.push_back(std::string(p));
			if(strlen(p) > VexSource::MAX_SRCNAME_LENGTH)
			{
				std::cerr << "Source name " << src << " is longer than " << VexSource::MAX_SRCNAME_LENGTH << "  characters!" << std::endl;
				++nWarn;
			}
		}

		p = (char *)get_source_lowl(src, T_SOURCE_TYPE, v);
		if(p)
		{
			int link, name;
			char *arg1 = 0, *arg2 = 0, *arg3 = 0, *units = 0;
			bool ok;

			vex_field(T_SOURCE_TYPE, p, 1, &link, &name, &arg1, &units); // first field
			vex_field(T_SOURCE_TYPE, p, 2, &link, &name, &arg2, &units); // second field
			vex_field(T_SOURCE_TYPE, p, 3, &link, &name, &arg3, &units); // third field

			ok = S->setSourceType(arg1, arg2, arg3);
			if(!ok && V->getVersion() < 1.8)
			{
				S->setBSP(arg1, atoi(arg2));	// A hack used pre-Vex2 at VLBA
			}

			if(V->getVersion() >= 1.8)
			{
				if(S->type == VexSource::BSP)
				{
		// FIXME: this is not working yet
					arg1 = arg2 = 0;
					vex_field(T_BSP_FILE_NAME, p, 1, &link, &name, &arg1, &units);
					vex_field(T_BSP_OBJECT_ID, p, 1, &link, &name, &arg2, &units);

					if(arg1 && arg2)
					{
						S->setBSP(arg1, atoi(arg2));
					}
				}
				else if(S->type == VexSource::TLE)
				{
		// FIXME: this is not working yet
					char *arg0 = 0;

					arg1 = arg2 = 0;
					vex_field(T_TLE0, p, 1, &link, &name, &arg0, &units);
					vex_field(T_TLE1, p, 1, &link, &name, &arg1, &units);
					vex_field(T_TLE2, p, 1, &link, &name, &arg2, &units);

					if(arg0)
					{
						S->setTLE(0, arg0);
					}
					if(arg1)
					{
						S->setTLE(0, arg1);
					}
					if(arg2)
					{
						S->setTLE(0, arg2);
					}
				}
			}
		}
		else
		{
			// default is to configure as a "star" type
			S->setSourceType("star");
		}

		if(S->type == VexSource::Star)
		{
			p = (char *)get_source_lowl(src, T_RA, v);
			if(!p)
			{
				std::cerr << "Error: Cannot find right ascension for source " << src << std::endl;

				exit(EXIT_FAILURE);
			}
			fvex_ra(&p, &S->ra);

			p = (char *)get_source_lowl(src, T_DEC, v);
			if(!p)
			{
				std::cerr << "Error: Cannot find declination for source " << src << std::endl;

				exit(EXIT_FAILURE);
			}
			fvex_dec(&p, &S->dec);

			S->type = VexSource::Star;
		}

		if(S->type == VexSource::Unsupported)
		{
			std::cerr << "Warning: Source " << S->defName << " is of an unsupported source type" << std::endl;
			++nWarn;
		}

		p = (char *)get_source_lowl(src, T_REF_COORD_FRAME, v);
		if(!p)
		{
			std::cerr << "Warning: Cannot find ref coord frame for source " << src << std::endl;
			std::cerr << "Assuming J2000" << std::endl;

			++nWarn;
		}
		else if(strcmp(p, "J2000") != 0)
		{
			std::cerr << "Error: only J2000 ref frame is supported." << std::endl;

			exit(EXIT_FAILURE);
		}
	}

	return nWarn;
}

static int getScans(VexData *V, Vex *v)
{
	char *scanId;
	int nWarn = 0;

	for(Llist *L = (Llist *)get_scan(&scanId, v); L != 0; L = (Llist *)get_scan_next(&scanId))
	{
		VexScan *S;
		std::map<std::string,bool> recordEnable;
		std::map<std::string,Interval> stations;
		double startScan, stopScan;
		double mjd;
		int link, name;
		char *value, *units;
		void *p;
		std::string intent = "";
		std::string tmpIntent;

		stations.clear();
		recordEnable.clear();

		Llist *lowls = L;
		lowls=find_lowl(lowls,T_COMMENT);
		while(lowls != NULL)
		{
			size_t pos;
			// assume our comments are clustered together at beginning of scan definition
			if(((Lowl *)lowls->ptr)->statement != T_COMMENT)
			{
				break;
			}
			// get comment content
			vex_field(T_COMMENT, (void *)((Lowl *)lowls->ptr)->item, 1, &link, &name, &value, &units);

			tmpIntent = (!value) ? "" : value;
			pos = tmpIntent.find("intent = \"", 0);
			if(pos != string::npos)
			{
				// +10 to skip the search string
				pos += 10;
				// trim everything except the actual tmpIntent string
				tmpIntent = tmpIntent.substr(pos, tmpIntent.size()-pos-1);
				intent += tmpIntent + ",";
			}
			lowls = lowls->next;
		}

		p = get_scan_start(L);

		vex_field(T_START, p, 1, &link, &name, &value, &units);
		mjd = vexDate(value);
		startScan = 1e99;
		stopScan = 0.0;
		for(p = get_station_scan(L); p; p = get_station_scan_next())
		{
			std::string stationName;
			double startAnt, stopAnt;
			char *stn;
			
			vex_field(T_STATION, p, 1, &link, &name, &stn, &units);
			stationName = std::string(stn);
			Upper(stationName);

			vex_field(T_STATION, p, 2, &link, &name, &value, &units);
			fvex_double(&value, &units, &startAnt);
			startAnt = mjd + startAnt/86400.0;	// mjd of antenna start
			if(startAnt < startScan)
			{
				startScan = startAnt;
			}

			vex_field(T_STATION, p, 3, &link, &name, &value, &units);
			fvex_double(&value, &units, &stopAnt);
			stopAnt = mjd + stopAnt/86400.0;	// mjd of antenna stop
			if(stopAnt > stopScan)
			{
				stopScan = stopAnt;
			}

			vex_field(T_STATION, p, 7, &link, &name, &value, &units);
			recordEnable[stationName] = (atoi(value) > 0);

			stations[stationName] = Interval(startAnt, stopAnt);
		}

		std::string scanDefName(scanId);
		std::string sourceDefName((char *)get_scan_source(L));
		std::string modeDefName((char *)get_scan_mode(L));

		const VexSource *src = V->getSourceByDefName(sourceDefName);
		if(src == 0)
		{
			std::cerr << "Vex error! Scan " << scanDefName << " references source " << sourceDefName << " which is not in the source table." << std::endl;

			exit(EXIT_FAILURE);
		}

		// Make scan
		S = V->newScan();
		S->setTimeRange(Interval(startScan, stopScan));
		S->defName = scanDefName;
		S->stations = stations;
		S->recordEnable = recordEnable;
		S->modeDefName = modeDefName;
		S->sourceDefName = sourceDefName;
		S->intent = intent;
		S->mjdVex = mjd;
	}

	return nWarn;
}

static VexSetup::SetupType getSetupType(Vex *v, const char *antDefName, const char *modeDefName)
{
	// Look for things needed for all kinds of modes
	if(get_all_lowl(antDefName, modeDefName, T_IF_DEF, B_IF, v) == 0 ||
	   get_all_lowl(antDefName, modeDefName, T_BBC_ASSIGN, B_BBC, v) == 0 ||
	   get_all_lowl(antDefName, modeDefName, T_CHAN_DEF, B_FREQ, v) == 0)
	{
		return VexSetup::SetupIncomplete;
	}

	if(get_all_lowl(antDefName, modeDefName, T_STREAM_DEF, B_BITSTREAMS, v))
	{
		// looks like bitstream; make sure supporting defs are in place

		return VexSetup::SetupBitstreams;
	}
	else if(get_all_lowl(antDefName, modeDefName, T_MERGED_DATASTREAM, B_DATASTREAMS, v))
	{
		return VexSetup::SetupMergedDatastreams;
	}
	else if(get_all_lowl(antDefName, modeDefName, T_DATASTREAM, B_DATASTREAMS, v))
	{
		return VexSetup::SetupDatastreams;
	}
	else if(get_all_lowl(antDefName, modeDefName, T_TRACK_FRAME_FORMAT, B_TRACKS, v))
	{
		if(get_all_lowl(antDefName, modeDefName, T_S2_RECORDING_MODE, B_TRACKS, v))
		{
			std::cerr << "Note: Both track frame format and s2 recording mode were specified.  S2 information will be ignored." << std::endl;
		}

		return VexSetup::SetupTracks;
	}
	else if(get_all_lowl(antDefName, modeDefName, T_S2_RECORDING_MODE, B_TRACKS, v))
	{
		return VexSetup::SetupS2;
	}

	return VexSetup::SetupIncomplete;
}

static int collectIFInfo(VexSetup &setup, VexData *V, Vex *v, const char *antDefName, const char *modeDefName)
{
	int nWarn = 0;
	void *p2array[MAX_IF];
	int p2count = 0;

	for(int i = 0; i < MAX_IF; ++i)
	{
		p2array[i] = 0;
	}

	for(void *p = get_all_lowl(antDefName, modeDefName, T_IF_DEF, B_IF, v); p; p = get_all_lowl_next())
	{
		double phaseCal, phaseCalBase;
		int link, name;
		char *value, *units;
		void *p2;
		
		vex_field(T_IF_DEF, p, 1, &link, &name, &value, &units);
		VexIF &vif = setup.ifs[std::string(value)];

		if(V->getVersion() < 2.0)
		{
			vex_field(T_IF_DEF, p, 2, &link, &name, &value, &units);
			vif.name = value;
		}
		else
		{
			if(strncmp(value, "IF_", 3) == 0)
			{
				vif.name = value + 3;
			}
			else
			{
				vif.name = value;
			}
		}
		
		vex_field(T_IF_DEF, p, 3, &link, &name, &value, &units);
		vif.pol = value[0];

		vex_field(T_IF_DEF, p, 4, &link, &name, &value, &units);
		fvex_double(&value, &units, &vif.ifSSLO);

		vex_field(T_IF_DEF, p, 5, &link, &name, &value, &units);
		vif.ifSideBand = value[0];

		vex_field(T_IF_DEF, p, 6, &link, &name, &value, &units);
		if(value)
		{
			fvex_double(&value, &units, &phaseCal);
		}
		else
		{
			phaseCal = 0.0;
		}
		if(fabs(phaseCal) < 1.0)
		{
			vif.phaseCalIntervalMHz = 0.0f;
		}
		else if(fabs(phaseCal-1000000.0) < 1.0)
		{
			vif.phaseCalIntervalMHz = 1.0f;
		}
		else if(fabs(phaseCal-5000000.0) < 1.0)
		{
			vif.phaseCalIntervalMHz = 5.0f;
		}
		else if(fabs(phaseCal-200000000.0) < 1.0)
		{
			vif.phaseCalIntervalMHz = 200.0f;
		}
		else
		{
			std::cerr << "Warning: Unsupported pulse cal interval of " << (phaseCal/1000000.0) << " MHz requested for antenna " << antDefName << "." << std::endl;
			++nWarn;
			vif.phaseCalIntervalMHz = static_cast<float>(phaseCal/1000000.0);
		}

		vex_field(T_IF_DEF, p, 7, &link, &name, &value, &units);
		if(value)
		{
			fvex_double(&value, &units, &phaseCalBase);
		}
		else
		{
			phaseCalBase = 0.0;
		}
		vif.phaseCalBaseMHz = static_cast<float>(phaseCalBase/1000000.0);


		if(p2count >= MAX_IF)
		{
			std::cerr << "Developer error: Value of MAX_IF is too small in vexload.cpp, instance 2" << std::endl;

			exit(0);
		}
		p2 = p2array[p2count++];

		// carry comment forward as it might contain information about IF
		vex_field(T_COMMENT, p2, 1, &link, &name, &value, &units);
		if(value)
		{
			vif.comment = value;
		} 
		else
		{
			vif.comment = "\0";
		}
	}

	return nWarn;
}

// FIXME: common code for pulse cal info
static int collectPcalInfo(std::map<std::string,std::vector<unsigned int> > &pcalMap, VexData *V, Vex *v, const char *antDefName, const char *modeDefName)
{
	int nWarn = 0;

	pcalMap.clear();

	for(void *p = get_all_lowl(antDefName, modeDefName, T_PHASE_CAL_DETECT, B_PHASE_CAL_DETECT, v); p; p = get_all_lowl_next())
	{
		int link, name;
		char *value, *units;

		vex_field(T_PHASE_CAL_DETECT, p, 1, &link, &name, &value, &units);
		std::vector<unsigned int> &Q = pcalMap[std::string(value)];
		
		for(int q = 2; ; ++q)
		{
			int v, y;
			
			y = vex_field(T_PHASE_CAL_DETECT, p, q, &link, &name, &value, &units);
			if(y < 0)
			{
				break;
			}
			
			v = atoi(value);
			if(v == 0)
			{
				// zero value implies next value indicates state counting
				++q;
			}
			else
			{
				// Move from vex's 1-based tones to DiFX's 0-based; negative tone numbers don't change
				int difxToneId = (v > 1) ? (v - 1) : v;
				Q.push_back(difxToneId);
			}
		}
		sort(Q.begin(), Q.end());
	}

	return nWarn;
}

// collect channel information from a $FREQ section
void getFreqChannels(std::vector<VexChannel> &freqChannels, VexSetup &setup, VexMode *M, Vex *v, const char *antDefName, const char *modeDefName)
{
	std::map<std::string,char> bbc2pol;
	std::map<std::string,std::string> bbc2ifName;
	int link, name;
	char *value, *units;

	// Get BBC to pol map; only needed to complete the frequency channel info
	for(void *p = get_all_lowl(antDefName, modeDefName, T_BBC_ASSIGN, B_BBC, v); p; p = get_all_lowl_next())
	{
		vex_field(T_BBC_ASSIGN, p, 3, &link, &name, &value, &units);
		VexIF &vif = setup.ifs[std::string(value)];

		vex_field(T_BBC_ASSIGN, p, 1, &link, &name, &value, &units);
		bbc2pol[value] = vif.pol;
		bbc2ifName[value] = vif.name;
	}

	freqChannels.clear();

	for(void *p = get_all_lowl(antDefName, modeDefName, T_CHAN_DEF, B_FREQ, v); p; p = get_all_lowl_next())
	{
		int recChanId;
		int subbandId;
		char *bbcName;
		double freq;
		double bandwidth;
		std::string chanName;
		std::string chanLinkName;
		std::string phaseCalName;

		vex_field(T_CHAN_DEF, p, 2, &link, &name, &value, &units);
		fvex_double(&value, &units, &freq);

		vex_field(T_CHAN_DEF, p, 3, &link, &name, &value, &units);
		char sideBand = value[0];
		
		vex_field(T_CHAN_DEF, p, 4, &link, &name, &value, &units);
		fvex_double(&value, &units, &bandwidth);

		vex_field(T_CHAN_DEF, p, 5, &link, &name, &value, &units);
		chanLinkName = value;

		vex_field(T_CHAN_DEF, p, 6, &link, &name, &bbcName, &units);
		subbandId = M->addSubband(freq, bandwidth, sideBand, bbc2pol[bbcName]);

		vex_field(T_CHAN_DEF, p, 7, &link, &name, &value, &units);
		phaseCalName = value;

		vex_field(T_CHAN_DEF, p, 8, &link, &name, &value, &units);
		if(value)
		{
			chanName = value;
		}
		else // Fall back to hack use of the BBC link name as the channel name
		{
			chanName = chanLinkName;
		}

		freqChannels.push_back(VexChannel());
		freqChannels.back().subbandId = subbandId;
		freqChannels.back().ifName = bbc2ifName[bbcName];
		freqChannels.back().bbcFreq = freq;
		freqChannels.back().bbcBandwidth = bandwidth;
		freqChannels.back().bbcSideBand = sideBand;
		freqChannels.back().bbcName = bbcName;
		freqChannels.back().name = chanName;
		freqChannels.back().linkName = chanLinkName;
		freqChannels.back().recordChan = -1;
		freqChannels.back().phaseCalName = phaseCalName;
	}
}

VexChannel *getVexChannelByLinkName(std::vector<VexChannel> &freqChannels, const std::string link)
{
	for(std::vector<VexChannel>::iterator it = freqChannels.begin(); it != freqChannels.end(); ++it)
	{
		if(it->linkName == link)
		{
			return &(*it);
		}
	}

	return 0;
}


static int getTracksSetup(VexSetup &setup, VexMode *M, VexData *V, Vex *v, const char *antDefName, const char *modeDefName, std::map<std::string,std::vector<unsigned int> > &pcalMap)
{
	VexStream &stream = setup.streams[0];	// the first stream is created by default
	int nWarn = 0;
	int link, name;
	char *value, *units;
	void *p;
	void *trackFormat;
	std::map<std::string,char> bbc2pol;
	std::map<std::string,std::string> bbc2ifName;
	std::map<std::string,BitAssignments> ch2tracks;
	int nBit = 1;
	int nTrack = 0;

	p = get_all_lowl(antDefName, modeDefName, T_SAMPLE_RATE, B_FREQ, v);
	if(p)
	{
		vex_field(T_SAMPLE_RATE, p, 1, &link, &name, &value, &units);
		fvex_double(&value, &units, &stream.sampRate);
	}

	// Get BBC to pol map for this antenna
	for(p = get_all_lowl(antDefName, modeDefName, T_BBC_ASSIGN, B_BBC, v); p; p = get_all_lowl_next())
	{
		vex_field(T_BBC_ASSIGN, p, 3, &link, &name, &value, &units);
		VexIF &vif = setup.ifs[std::string(value)];

		vex_field(T_BBC_ASSIGN, p, 1, &link, &name, &value, &units);
		bbc2pol[value] = vif.pol;
		bbc2ifName[value] = vif.name;
	}

	trackFormat = get_all_lowl(antDefName, modeDefName, T_TRACK_FRAME_FORMAT, B_TRACKS, v);

	vex_field(T_TRACK_FRAME_FORMAT, trackFormat, 1, &link, &name, &value, &units);
	stream.parseFormatString(value);

	if(stream.isLBAFormat())
	{
		for(p = get_all_lowl(antDefName, modeDefName, T_FANOUT_DEF, B_TRACKS, v); p; p = get_all_lowl_next())
		{
			std::string chanName;
			bool sign;
			int dasNum;

			vex_field(T_FANOUT_DEF, p, 2, &link, &name, &value, &units);
			chanName = value;
			vex_field(T_FANOUT_DEF, p, 3, &link, &name, &value, &units);
			sign = (value[0] == 's');
			vex_field(T_FANOUT_DEF, p, 4, &link, &name, &value, &units);
			sscanf(value, "%d", &dasNum);

			int chanNum;

			if(vex_field(T_FANOUT_DEF, p, 5, &link, &name, &value, &units) < 0)
			{
				break;
			}
			sscanf(value, "%d", &chanNum);
			chanNum += 32*(dasNum-1);
			if(sign)
			{
				ch2tracks[chanName].sign.push_back(chanNum);
			}
			else
			{
				nBit = 2;
				ch2tracks[chanName].mag.push_back(chanNum);
			}
		}
		stream.nRecordChan = ch2tracks.size();
		stream.nBit = nBit;
	}
	else
	{
		for(p = get_all_lowl(antDefName, modeDefName, T_FANOUT_DEF, B_TRACKS, v); p; p = get_all_lowl_next())
		{
			std::string chanName;
			bool sign;
			int dasNum;
			
			vex_field(T_FANOUT_DEF, p, 2, &link, &name, &value, &units);
			chanName = value;
			vex_field(T_FANOUT_DEF, p, 3, &link, &name, &value, &units);
			sign = (value[0] == 's');
			vex_field(T_FANOUT_DEF, p, 4, &link, &name, &value, &units);
			sscanf(value, "%d", &dasNum);

			for(int k = 5; k < 9; ++k)
			{
				int chanNum;
				
				if(vex_field(T_FANOUT_DEF, p, k, &link, &name, &value, &units) < 0)
				{
					break;
				}
				++nTrack;
				sscanf(value, "%d", &chanNum);
				chanNum += 32*(dasNum-1);
				if(sign)
				{
					ch2tracks[chanName].sign.push_back(chanNum);
				}
				else
				{
					if(stream.nBit == 0)
					{
						nBit = 2;
					}
					else
					{
						nBit = stream.nBit;
					}
					ch2tracks[chanName].mag.push_back(chanNum);
				}
			}
		}
		if(!ch2tracks.empty())
		{
			int fanout;

			fanout = nTrack/ch2tracks.size()/nBit;
			if(stream.formatHasFanout())
			{
				stream.setFanout(fanout);
			}

			// FIXME: what to do if nBit and nRecordChan already set but they disagree?

			stream.nRecordChan = ch2tracks.size();
			stream.nBit = nBit;
		}
	}

	if(stream.format == VexStream::FormatMark5B || stream.format == VexStream::FormatKVN5B)
	{
		// Because Mark5B formatters can apply a bitmask, the track numbers may not be contiguous.  Here we go through and reorder track numbers in sequence, starting with 2
		reorderBitAssignments(ch2tracks, 2);
	}

	// Get rest of Subband information
	unsigned int nRecordChan = 0;
	
	for(p = get_all_lowl(antDefName, modeDefName, T_CHAN_DEF, B_FREQ, v); p; p = get_all_lowl_next())
	{
		int recChanId;
		int subbandId;
		char *bbcName;
		double freq;
		double bandwidth;
		std::string chanName;

		vex_field(T_CHAN_DEF, p, 2, &link, &name, &value, &units);
		fvex_double(&value, &units, &freq);

		vex_field(T_CHAN_DEF, p, 3, &link, &name, &value, &units);
		char sideBand = value[0];
		
		vex_field(T_CHAN_DEF, p, 4, &link, &name, &value, &units);
		fvex_double(&value, &units, &bandwidth);

		if(bandwidth - stream.sampRate/2 > 1e-6)
		{
			std::cerr << "Error: " << modeDefName << " antenna " << antDefName << " has sample rate = " << stream.sampRate << " bandwidth = " << bandwidth << std::endl;
			std::cerr << "Sample rate must be no less than twice the bandwidth in all cases." << std::endl;

// FIXME: replace this later					exit(EXIT_FAILURE);
		}

		if(bandwidth - stream.sampRate/2 < -1e-6)
		{
			// Note: this is tested in a sanity check later.  This behavior is not always desirable.
			bandwidth = stream.sampRate/2;
		}

		vex_field(T_CHAN_DEF, p, 6, &link, &name, &bbcName, &units);
		subbandId = M->addSubband(freq, bandwidth, sideBand, bbc2pol[bbcName]);

		vex_field(T_CHAN_DEF, p, 7, &link, &name, &value, &units);
		std::string phaseCalName(value);

		vex_field(T_CHAN_DEF, p, 8, &link, &name, &value, &units);
		if(value)
		{
			chanName = value;
		}
		else // Fall back to hack use of the BBC link name as the channel name
		{
			vex_field(T_CHAN_DEF, p, 5, &link, &name, &value, &units);
			chanName = value;
		}
		recChanId = getRecordChannelFromTracks(antDefName, chanName, ch2tracks, stream, nRecordChan);

		setup.channels.push_back(VexChannel());
		setup.channels.back().subbandId = subbandId;
		setup.channels.back().ifName = bbc2ifName[bbcName];
		setup.channels.back().bbcFreq = freq;
		setup.channels.back().bbcBandwidth = bandwidth;
		setup.channels.back().bbcSideBand = sideBand;
		setup.channels.back().bbcName = bbcName;
		setup.channels.back().name = chanName;
		setup.channels.back().phaseCalName = phaseCalName;
		if(recChanId >= 0)
		{
			setup.channels.back().recordChan = recChanId;
			setup.channels.back().tones = pcalMap[phaseCalName];
		}
		else
		{
			setup.channels.back().recordChan = -1;
		}

		++nRecordChan;
	}

	if(stream.nRecordChan == 0)	// then use the number of that we just counted out
	{
		if(stream.nThread() > 1)
		{
			// Test that nThread divides into nRecordChan
			if(nRecordChan % stream.nThread() != 0)
			{
				std::cerr << "Error: " << modeDefName << " antenna " << antDefName << " number of threads (" << stream.nThread() << ") does not divide into number of record channels (" << nRecordChan << ")." << std::endl;

				exit(EXIT_FAILURE);
			}
		}
		stream.nRecordChan = nRecordChan;
	}

	if(stream.isVDIFFormat())
	{
		// Sort channels by name and then assign sequential thread Id
		std::sort(setup.channels.begin(), setup.channels.end());
		for(unsigned int recChan = 0; recChan < setup.channels.size(); ++recChan)
		{
			setup.channels[recChan].threadId = recChan;
			setup.channels[recChan].recordChan = recChan;
		}
	}

	return nWarn;
}

static int getBitstreamsSetup(VexSetup &setup, VexMode *M, VexData *V, Vex *v, const char *antDefName, const char *modeDefName, std::map<std::string,std::vector<unsigned int> > &pcalMap)
{
	const int MaxBitstreams = 64;
	VexStream &stream = setup.streams[0];	// the first stream is created by default
	int nWarn = 0;
	int link, name;
	char *value, *units;
	void *p;
	std::map<std::string,char> bbc2pol;
	std::map<std::string,std::string> bbc2ifName;
	std::map<std::string,BitAssignments> ch2bitstreams;
	int nBit = 1;
	int nBitstream = 0;

	p = get_all_lowl(antDefName, modeDefName, T_STREAM_SAMPLE_RATE, B_BITSTREAMS, v);
	if(p)
	{
		vex_field(T_STREAM_SAMPLE_RATE, p, 1, &link, &name, &value, &units);
		fvex_double(&value, &units, &stream.sampRate);
	}

	// Get BBC to pol map for this antenna
	for(p = get_all_lowl(antDefName, modeDefName, T_BBC_ASSIGN, B_BBC, v); p; p = get_all_lowl_next())
	{
		vex_field(T_BBC_ASSIGN, p, 3, &link, &name, &value, &units);
		VexIF &vif = setup.ifs[std::string(value)];

		vex_field(T_BBC_ASSIGN, p, 1, &link, &name, &value, &units);
		bbc2pol[value] = vif.pol;
		bbc2ifName[value] = vif.name;
	}

	// Only Mark5B format is supported when using BITSTREAMS
	stream.parseFormatString("MARK5B");

	for(p = get_all_lowl(antDefName, modeDefName, T_STREAM_DEF, B_BITSTREAMS, v); p; p = get_all_lowl_next())
	{
		std::string chanName;
		bool sign;
		int bitstreamNum;
		
		vex_field(T_STREAM_DEF, p, 1, &link, &name, &value, &units);
		chanName = value;
		vex_field(T_STREAM_DEF, p, 2, &link, &name, &value, &units);
		sign = (value[0] == 's');
		vex_field(T_STREAM_DEF, p, 4, &link, &name, &value, &units);
		sscanf(value, "%d", &bitstreamNum);

		if(bitstreamNum < 0 || bitstreamNum >= MaxBitstreams)
		{
			std::cerr << "Error: Antenna " << antDefName << " Mode " << modeDefName << " Chan " << chanName << " has bitstream number out of range." << std::endl;
			std::cerr << "  bitstream number was " << bitstreamNum << " but it must be in [0.." << (MaxBitstreams-1) << "] inclusive." << std::endl;
			exit(0);
		}

		++nBitstream;
		if(sign)
		{
			ch2bitstreams[chanName].sign.push_back(bitstreamNum);
		}
		else
		{
			nBit = 2;
			ch2bitstreams[chanName].mag.push_back(bitstreamNum);
		}
	}
	if(ch2bitstreams.empty())
	{
		std::cerr << "Error: Antenna " << antDefName << " Mode " << modeDefName << " has no bitstreams defined." << std::endl;
		exit(0);
	}

	stream.nBit = nBit;
	stream.nRecordChan = ch2bitstreams.size();
	// verify sign-mag are all consecutive and sanely populated
	if(nBit == 2)
	{
		for(std::map<std::string,BitAssignments>::const_iterator it = ch2bitstreams.begin(); it != ch2bitstreams.end(); ++it)
		{
			const BitAssignments &ba = it->second;
			if(ba.sign.size() != 1 || ba.mag.size() != 1)
			{
				std::cerr << "Error: Antenna " << antDefName << " Mode " << modeDefName << " Chan " << it->first << " does not have exactly one sign and one mag bit assigned." << std::endl;
				std::cerr << "  nSign = " << ba.sign.size() <<" nMag = " << ba.mag.size() << std::endl;
				exit(0);
			}
			else if(ba.mag[0] != ba.sign[0] + 1 || ba.sign[0] % 2 == 1)
			{
				std::cerr << "Error: Antenna " << antDefName << " Mode " << modeDefName << " Chan " << it->first << " violates vex2difx's constraint on bit stream assignments." << std::endl;
				std::cerr << "  2-bit data must have the sign bit on an even channel with the magnitude bit in the next bitstream." << std::endl;
				std::cerr << "  Sign assignment = " << ba.sign[0] <<" Mag assignemnt = " << ba.mag[0] << std::endl;
				exit(0);
			}
		}
	}
	else
	{
		for(std::map<std::string,BitAssignments>::const_iterator it = ch2bitstreams.begin(); it != ch2bitstreams.end(); ++it)
		{
			const BitAssignments &ba = it->second;
			if(ba.sign.size() != 1 || ba.mag.size() != 0)
			{
				std::cerr << "Error: Antenna " << antDefName << " Mode " << modeDefName << " Chan " << it->first << " does not have exactly one sign and zero mag bit assigned." << std::endl;
				std::cerr << "  nSign = " << ba.sign.size() <<" nMag = " << ba.mag.size() << std::endl;
				exit(0);
			}
		}
	}

	// Because Mark5B formatters can apply a bitmask, the track numbers may not be contiguous.  Here we go through and reorder track numbers in sequence, starting with 2
	reorderBitAssignments(ch2bitstreams, 0);

	// Get rest of Subband information
	unsigned int nRecordChan = 0;
	
	for(p = get_all_lowl(antDefName, modeDefName, T_CHAN_DEF, B_FREQ, v); p; p = get_all_lowl_next())
	{
		int recChanId;
		int subbandId;
		char *bbcName;
		double freq;
		double bandwidth;
		std::string chanName;
		std::string chanLinkName;

		vex_field(T_CHAN_DEF, p, 2, &link, &name, &value, &units);
		fvex_double(&value, &units, &freq);

		vex_field(T_CHAN_DEF, p, 3, &link, &name, &value, &units);
		char sideBand = value[0];
		
		vex_field(T_CHAN_DEF, p, 4, &link, &name, &value, &units);
		fvex_double(&value, &units, &bandwidth);

		if(bandwidth - stream.sampRate/2 > 1e-6)
		{
			std::cerr << "Error: " << modeDefName << " antenna " << antDefName << " has sample rate = " << stream.sampRate << " bandwidth = " << bandwidth << std::endl;
			std::cerr << "Sample rate must be no less than twice the bandwidth in all cases." << std::endl;

			exit(EXIT_FAILURE);
		}

		if(bandwidth - stream.sampRate/2 < -1e-6)
		{
			// Note: this is tested in a sanity check later.  This behavior is not always desirable.
			bandwidth = stream.sampRate/2;
		}

		vex_field(T_CHAN_DEF, p, 5, &link, &name, &value, &units);
		chanLinkName = value;

		vex_field(T_CHAN_DEF, p, 6, &link, &name, &bbcName, &units);
		subbandId = M->addSubband(freq, bandwidth, sideBand, bbc2pol[bbcName]);

		vex_field(T_CHAN_DEF, p, 7, &link, &name, &value, &units);
		std::string phaseCalName(value);

		vex_field(T_CHAN_DEF, p, 8, &link, &name, &value, &units);
		if(value)
		{
			chanName = value;
		}
		else // Fall back to hack use of the BBC link name as the channel name
		{
			chanName = chanLinkName;
		}
		recChanId = getRecordChannelFromBitstreams(antDefName, chanName, ch2bitstreams, stream, nRecordChan);

		setup.channels.push_back(VexChannel());
		setup.channels.back().subbandId = subbandId;
		setup.channels.back().ifName = bbc2ifName[bbcName];
		setup.channels.back().bbcFreq = freq;
		setup.channels.back().bbcBandwidth = bandwidth;
		setup.channels.back().bbcSideBand = sideBand;
		setup.channels.back().bbcName = bbcName;
		setup.channels.back().name = chanName;
		setup.channels.back().linkName = chanLinkName;
		setup.channels.back().phaseCalName = phaseCalName;
		if(recChanId >= 0)
		{
			setup.channels.back().recordChan = recChanId;
			setup.channels.back().tones = pcalMap[phaseCalName];
		}
		else
		{
			setup.channels.back().recordChan = -1;
		}

		++nRecordChan;
	}

	return nWarn;
}

static int getDatastreamsSetup(VexSetup &setup, VexMode *M, VexData *V, Vex *v, const char *antDefName, const char *modeDefName, std::map<std::string,std::vector<unsigned int> > &pcalMap)
{
	int nWarn = 0;
	int link, name;
	char *value, *units;
	void *p;
	std::vector<VexChannel> freqChannels;		// list of channels from relevant $FREQ section
	int nStream = 0;	

	// Get list of channels from $FREQ
	getFreqChannels(freqChannels, setup, M, v, antDefName, modeDefName);
	
	// Loop over datastreams
	for(p = get_all_lowl(antDefName, modeDefName, T_DATASTREAM, B_DATASTREAMS, v); p; p = get_all_lowl_next())
	{
		if(nStream > 0)
		{
			setup.streams.push_back(VexStream());
		}

		VexStream &stream = setup.streams[nStream];

		vex_field(T_DATASTREAM, p, 1, &link, &name, &value, &units);
		if(!value)
		{
			std::cerr << "YIKES 1" << std::endl;

			exit(0);
		}
		stream.linkName = value;

		vex_field(T_DATASTREAM, p, 2, &link, &name, &value, &units);
		if(!value)
		{
			std::cerr << "YIKES 2" << std::endl;

			exit(0);
		}
		if(strcasecmp(value, "VDIF") == 0)
		{
			stream.parseFormatString("VDIF");
		}
		else if(strcasecmp(value, "VDIF_legacy") == 0)
		{
			stream.parseFormatString("VDIFL");
		}
		else if(strcasecmp(value, "CODIF") == 0)
		{
			stream.parseFormatString("CODIF");
		}

		stream.threads.clear();	// Just make sure these are left undefined; they will be completely defined in the code that follows

		vex_field(T_DATASTREAM, p, 3, &link, &name, &value, &units);
		if(value && strlen(value) > 0)
		{
			stream.label = value;
		}

		++nStream;
	}

	// Loop over threads
	for(p = get_all_lowl(antDefName, modeDefName, T_THREAD, B_DATASTREAMS, v); p; p = get_all_lowl_next())
	{
		VexStream *stream;
		int threadId;
		char *threadLinkName;

		vex_field(T_THREAD, p, 1, &link, &name, &value, &units);
		if(!value)
		{
			std::cerr << "YIKES 3" << std::endl;

			exit(0);
		}
		stream = setup.getVexStreamByLinkName(value);
		if(!stream)
		{
			std::cerr << "YIKES 4" << std::endl;

			exit(0);
		}

		vex_field(T_THREAD, p, 3, &link, &name, &value, &units);
		threadId = atoi(value);
		if(find(stream->threads.begin(), stream->threads.end(), threadId) != stream->threads.end())
		{
			// Bad: thread was already part of the stream
			std::cerr << "YIKES 7" << std::endl;

			exit(0);
		}
		stream->threads.push_back(VexThread(threadId));
		VexThread &T = stream->threads.back();
		if(stream->nThread() > 1)
		{
			stream->singleThread = false;
		}

		vex_field(T_THREAD, p, 2, &link, &name, &value, &units);
		threadLinkName = value;
		T.linkName = threadLinkName;

		vex_field(T_THREAD, p, 4, &link, &name, &value, &units);
		T.nChan = atoi(value);
		stream->nRecordChan += T.nChan;

		vex_field(T_THREAD, p, 5, &link, &name, &value, &units);
		fvex_double(&value, &units, &T.sampRate);
		if(stream->sampRate == 0.0)
		{
			stream->sampRate = T.sampRate;
		}
		else if(stream->sampRate != T.sampRate)
		{
			std::cerr << "YIKES 5" << std::endl;

			exit(0);
		}

		vex_field(T_THREAD, p, 6, &link, &name, &value, &units);
		T.nBit = atoi(value);
		if(stream->nBit == 0)
		{
			stream->nBit = T.nBit;
		}
		else if(stream->nBit != T.nBit)
		{
			std::cerr << "YIKES 6" << std::endl;

			exit(0);
		}

		vex_field(T_THREAD, p, 7, &link, &name, &value, &units);
		if(value)
		{
			if(strcasecmp(value, "real") == 0)
			{
				stream->dataSampling = SamplingReal;
			}
			else if(strcasecmp(value, "complex") == 0)
			{
				stream->dataSampling = SamplingComplex;
			}
			else if(strcasecmp(value, "complexDSB") == 0)
			{
				stream->dataSampling = SamplingComplexDSB;
			}
			else
			{
				std::cerr << "YIKES 8" << std::endl;

				exit(0);
			}
		}

		vex_field(T_THREAD, p, 8, &link, &name, &value, &units);
		T.dataBytes = atoi(value);
		if(stream->format == VexStream::FormatLegacyVDIF)
		{
			stream->VDIFFrameSize = T.dataBytes + 16;
		}
		else
		{
			stream->VDIFFrameSize = T.dataBytes + 32;
		}
	}

	// Go through each datastream: sort threadId list and set startRecordChan for each
	for(std::vector<VexStream>::iterator it = setup.streams.begin(); it != setup.streams.end(); ++it)
	{
		int startRecordChan;

		startRecordChan = 0;
		sort(it->threads.begin(), it->threads.end());
		for(std::vector<VexThread>::iterator t = it->threads.begin(); t != it->threads.end(); ++t)
		{
			t->startRecordChan = startRecordChan;
			startRecordChan += t->nChan;
		}
	}

	// Loop over channels
	for(p = get_all_lowl(antDefName, modeDefName, T_CHANNEL, B_DATASTREAMS, v); p; p = get_all_lowl_next())
	{
		VexStream *stream;
		VexThread *thread;
		VexChannel *channel;
		char *chanLink;
		int threadChan;

		vex_field(T_CHANNEL, p, 1, &link, &name, &value, &units);
		if(!value)
		{
			std::cerr << "YIKES 11" << std::endl;

			exit(0);
		}
		stream = setup.getVexStreamByLinkName(value);
		if(!stream)
		{
			std::cerr << "YIKES 12" << std::endl;

			exit(0);
		}

		vex_field(T_CHANNEL, p, 2, &link, &name, &value, &units);
		if(!value)
		{
			std::cerr << "YIKES 13" << std::endl;

			exit(0);
		}
		thread = stream->getVexThreadByLinkName(value);
		if(!thread)
		{
			std::cerr << "YIKES 14" << std::endl;

			exit(0);
		}

		vex_field(T_CHANNEL, p, 3, &link, &name, &chanLink, &units);
		if(!chanLink || chanLink[0] == 0)
		{
			std::cerr << "YIKES 16" << std::endl;

			exit(0);
		}

		vex_field(T_CHANNEL, p, 4, &link, &name, &value, &units);
		if(!value)
		{
			std::cerr << "YIKES 17" << std::endl;

			exit(0);
		}
		threadChan = atoi(value);
		if(threadChan < 0 || threadChan >= thread->nChan)
		{
			std::cerr << "YIKES 18" << std::endl;

			exit(0);
		}

		channel = getVexChannelByLinkName(freqChannels, chanLink);
		if(!channel)
		{
			std::cerr << "YIKES 19" << std::endl;

			exit(0);
		}

		setup.channels.push_back(*channel);
		channel = &setup.channels.back();

		if(channel->bbcBandwidth - stream->sampRate/2 > 1e-6)
		{
			std::cerr << "Error: " << modeDefName << " antenna " << antDefName << " has sample rate = " << stream->sampRate << " bandwidth = " << channel->bbcBandwidth << std::endl;
			std::cerr << "Sample rate must be no less than twice the bandwidth in all cases." << std::endl;

			exit(EXIT_FAILURE);
		}

		if(channel->bbcBandwidth - stream->sampRate/2 < -1e-6)
		{
			// Note: this is tested in a sanity check later.  This behavior is not always desirable.
			channel->bbcBandwidth = stream->sampRate/2;
		}

		channel->recordChan = thread->startRecordChan + threadChan;
		channel->tones = pcalMap[channel->phaseCalName];
	}

	return nWarn;
}

/* 

Some things to do to clean things up

1. Capture contents of $FREQ early (use getFreqChannels()) in getModes()

2. All Setup readers should make use of this list

2. At end of getModes, unset unused tones

*/

static int getModes(VexData *V, Vex *v)
{
	int nWarn = 0;

	for(const char *modeDefName = get_mode_def(v); modeDefName; modeDefName = get_mode_def_next())
	{
		VexMode *M;
		
		// don't bother building up modes that are not used
		if(!V->usesMode(modeDefName))
		{
			continue;
		}

		M = V->newMode();
		M->defName = modeDefName;

		for(unsigned int a = 0; a < V->nAntenna(); ++a)
		{
			const std::string &antName = V->getAntenna(a)->defName;
			VexSetup::SetupType type;
			std::map<std::string,std::vector<unsigned int> > pcalMap;

			type = getSetupType(v, antName.c_str(), modeDefName);

			std::cout << "Setup(" << modeDefName << ", " << antName << ") has type " << VexSetup::setupTypeName[type] << std::endl;

			if(type == VexSetup::SetupIncomplete)
			{
				std::cerr << "Note: Incomplete description for " << antName << " in mode " << modeDefName << ". The vex file might need editing.  This antenna/mode will be ignored." << std::endl;
				continue;
			}

			// if we made it this far the antenna is involved in this mode
			VexSetup &setup = M->setups[V->getAntenna(a)->name];	// This creates the new entry

			setup.type = type;

			nWarn += collectIFInfo(setup, V, v, antName.c_str(), modeDefName);
			nWarn += collectPcalInfo(pcalMap, V, v, antName.c_str(), modeDefName);

			switch(type)
			{
			case VexSetup::SetupTracks:
				nWarn += getTracksSetup(setup, M, V, v, antName.c_str(), modeDefName, pcalMap);
				break;
			case VexSetup::SetupBitstreams:
				nWarn += getBitstreamsSetup(setup, M, V, v, antName.c_str(), modeDefName, pcalMap);
				break;
			case VexSetup::SetupDatastreams:
				nWarn += getDatastreamsSetup(setup, M, V, v, antName.c_str(), modeDefName, pcalMap);
				break;
			default:
				std::cerr << "Setup type " << VexSetup::setupTypeName[type] << " is not (yet) supported." << std::endl;
				++nWarn;
			}

		} // End of antenna loop
	} // End of mode loop

	return nWarn;
}

static int getVSN(VexData *V, Vex *v, const char *station)
{
	llist *block;
	Llist *defs;
	bool quit = false;

	std::string antName(station);

	Upper(antName);

	block = find_block(B_TAPELOG_OBS, v);

	if(!block)
	{
		return -1;
	}

	defs = ((struct block *)block->ptr)->items;
	if(!defs)
	{
		return -2;
	}

	defs = find_def(defs, station);
	if(!defs)
	{
		return -3;
	}

	for(Llist *lowls = find_lowl(((Def *)((Lowl *)defs->ptr)->item)->refs, T_VSN); lowls; lowls = lowls->next)
	{
		Vsn *p;
		int drive;

		if(((Lowl *)lowls->ptr)->statement != T_VSN)
		{
			continue;
		}
		
		p = (Vsn *)(((Lowl *)lowls->ptr)->item);
		if(!p)
		{
			return -4;
		}

		std::string vsn(p->label);
		fixOhs(vsn);

		drive = atoi(p->drive->value);

		Interval vsnTimeRange(vexDate(p->start)+0.001/86400.0, vexDate(p->stop));

		if(!vsnTimeRange.isCausal())
		{
			std::cerr << "Error: Record stop (" << p->stop << ") precedes record start (" << p->start << ") for antenna " << antName << ", module " << vsn << " ." << std::endl;
			quit = true;
		}
		else
		{
			if(vsn[0] == '/')
			{
				V->addFile(antName, drive, vsn, vsnTimeRange);
			}
			else
			{
				V->addVSN(antName, drive, vsn, vsnTimeRange);
			}
		}
	}

	if(quit)
	{
		exit(EXIT_FAILURE);
	}

	return 0;
}

static int getVSNs(VexData *V, Vex *v)
{
	int nWarn = 0;

	for(char *stn = get_station_def(v); stn; stn=get_station_def_next())
	{
		getVSN(V, v, stn);
	}

	return nWarn;
}

static int getEOPs(VexData *V, Vex *v)
{
	llist *block;
	int N = 0;
	int nWarn = 0;

	block = find_block(B_EOP, v);

	if(block)
	{
		for(Llist *defs=((struct block *)block->ptr)->items; defs; defs=defs->next)
		{
			int nEop;
			int statement;
			double refEpoch;
			Llist *lowls, *refs;
			int link, name;
			char *value, *units;
			double interval;
			dvalue *r;
			void *p;
			double tai_utc, ut1_utc, x_wobble, y_wobble;
			
			statement = ((Lowl *)defs->ptr)->statement;

			if(statement == T_COMMENT || statement == T_COMMENT_TRAILING)
			{
				continue;
			}
			if(statement != T_DEF)
			{
				break;
			}

			refs = ((Def *)((Lowl *)defs->ptr)->item)->refs;

			lowls = find_lowl(refs, T_TAI_UTC);
			r = (struct dvalue *)(((Lowl *)lowls->ptr)->item);
			fvex_double(&r->value, &r->units, &tai_utc);

			lowls = find_lowl(refs, T_EOP_REF_EPOCH);
			p = (((Lowl *)lowls->ptr)->item);
			refEpoch = vexDate((char *)p);

			lowls = find_lowl(refs, T_NUM_EOP_POINTS);
			r = (struct dvalue *)(((Lowl *)lowls->ptr)->item);
			nEop = atoi(r->value);
			N += nEop;

			lowls = find_lowl(refs, T_EOP_INTERVAL);
			r = (struct dvalue *)(((Lowl *)lowls->ptr)->item);
			fvex_double(&r->value, &r->units, &interval);

			for(int i = 0; i < nEop; ++i)
			{	
				VexEOP *E;
				
				lowls = find_lowl(refs, T_UT1_UTC);
				vex_field(T_UT1_UTC, ((Lowl *)lowls->ptr)->item, i+1, &link, &name, &value, &units);
				fvex_double(&value, &units, &ut1_utc);

				lowls = find_lowl(refs, T_X_WOBBLE);
				vex_field(T_X_WOBBLE, ((Lowl *)lowls->ptr)->item, i+1, &link, &name, &value, &units);
				fvex_double(&value, &units, &x_wobble);

				lowls = find_lowl(refs, T_Y_WOBBLE);
				vex_field(T_Y_WOBBLE, ((Lowl *)lowls->ptr)->item, i+1, &link, &name, &value, &units);
				fvex_double(&value, &units, &y_wobble);

				E = V->newEOP();
				E->mjd = refEpoch + i*interval/86400.0;
				E->tai_utc = tai_utc;
				E->ut1_utc = ut1_utc;
				E->xPole = x_wobble;
				E->yPole = y_wobble;
			}
		}
	}

	return nWarn;
}

static int getExper(VexData *V, Vex *v)
{
	llist *block;
	double start, stop;
	int nWarn = 0;

	start = V->getEarliestScanStart() - 1.0/86400.0;
	stop = V->getLatestScanStop() + 1.0/86400.0;

	if(v->version)
	{
		lowl *w;

		w = (lowl *)(v->version->ptr);

		V->setVersion((char *)(w->item));
	}
	else
	{
		std::cerr << "Warning: VEX_REV not set.  That is bad." << std::endl;

		++nWarn;
	}

	block = find_block(B_EXPER, v);

	if(!block)
	{
		std::cerr << "Warning: no EXPER block found in the vex file.  That is bad." << std::endl;

		V->setExper("RANDOM", Interval(start, stop));
		
		++nWarn;
	}
	else
	{
		std::string experimentName;
		
		for(Llist *defs=((struct block *)block->ptr)->items; defs; defs=defs->next)
		{
			int statement;
			Llist *lowls, *refs;
			Exper_name *en;
			
			statement = ((Lowl *)defs->ptr)->statement;
			if(statement == T_COMMENT || statement == T_COMMENT_TRAILING)
			{
				continue;
			}
			if(statement != T_DEF)
			{
				break;
			}

			refs = ((Def *)((Lowl *)defs->ptr)->item)->refs;

			lowls = find_lowl(refs, T_EXPER_NAME);

			en = (Exper_name *)(((Lowl *)lowls->ptr)->item);

			experimentName = en->name;

			lowls = find_lowl(refs, T_EXPER_NOMINAL_START);
			if(lowls)
			{
				void *p;
				
				p = (((Lowl *)lowls->ptr)->item);
				start = vexDate((char *)p);
				strncpy(V->vexStartTime, ((char *)p), 50);
				V->vexStartTime[4] = '\0';
				V->vexStartTime[8] = '\0';
				V->vexStartTime[11] = '\0';
				V->vexStartTime[14] = '\0';
				V->vexStartTime[17] = '\0';
			}
			else
			{
				std::cerr << "Note: The vex file has no exper_nominal_start parameter defined in the EXPER section.  Making assumptions..." << std::endl;
			}

			lowls = find_lowl(refs, T_EXPER_NOMINAL_STOP);
			if(lowls)
			{
				void *p;

				p = (((Lowl *)lowls->ptr)->item);
				stop = vexDate((char *)p);
				strncpy(V->vexStopTime, ((char *)p), 50);
				V->vexStopTime[4] = '\0';
				V->vexStopTime[8] = '\0';
				V->vexStopTime[11] = '\0';
				V->vexStopTime[14] = '\0';
				V->vexStopTime[17] = '\0';
			}
			else
			{
				std::cerr << "Note: The vex file has no exper_nominal_stop parameter defined in the EXPER section.  Making assumptions..." << std::endl;
			}
		}

		Upper(experimentName);

		V->setExper(experimentName, Interval(start, stop));
	}

	return nWarn;
}


VexData *loadVexFile(const std::string &vexFile, unsigned int *numWarnings)
{
	VexData *V;
	Vex *v;
	int r;
	int nWarn = 0;

	r = vex_open(vexFile.c_str(), &v);
	if(r != 0)
	{
		return 0;
	}

	V = new VexData();

	V->setDirectory(vexFile.substr(0, vexFile.find_last_of('/')));

	nWarn += getExper(V, v);
	nWarn += getAntennas(V, v);
	nWarn += getSources(V, v);
	nWarn += getScans(V, v);
	nWarn += getModes(V, v);
	nWarn += getVSNs(V, v);
	nWarn += getEOPs(V, v);
	*numWarnings = *numWarnings + nWarn;

	return V;
}
