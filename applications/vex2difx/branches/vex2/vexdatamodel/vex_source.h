/***************************************************************************
 *   Copyright (C) 2015-2021 by Walter Brisken & Adam Deller               *
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
 * $HeadURL: https://svn.atnf.csiro.au/difx/applications/vex2difx/branches/multidatastream_refactor/src/vex2difx.cpp $
 * $LastChangedRevision$
 * $Author$
 * $LastChangedDate$
 *
 *==========================================================================*/

#ifndef __VEX_SOURCE_H__
#define __VEX_SOURCE_H__

#include <iostream>
#include <string>
#include <vector>

class VexSource
{
public:
	enum Type { Star, EarthSatellite, BSP, TLE, Ephemeris, Unsupported };

	VexSource() : type(Unsupported), ra(0.0), dec(0.0), calCode(' ') {}
	VexSource(std::string name, double ra1, double dec1) : type(Star), defName(name), ra(ra1), dec(dec1), calCode(' ') {}
	bool hasSourceName(const std::string &name) const;
	bool setSourceType(const char *t1 = 0, const char *t2 = 0, const char *t3 = 0);
	void setTLE(int lineNum, const char *line);	// lineNum must be 0, 1 or 2
	void setBSP(const char *fileName, int objectId);

	enum Type type;

	std::string defName;				// in the "def ... ;" line in Vex
	std::string sourceType1;
	std::string sourceType2;
	std::string sourceType3;

	std::string tle[3];				// corresponds to rows 0 (20 chars), 1 (69 chars) and 2 (69 chars) of an embedded TLE

	std::string bspFile;
	int bspObject;
	
	std::vector<std::string> sourceNames;		// from source_name statements
	double ra;					// (rad)
	double dec;					// (rad)
	// FIXME: add "ref_coord_frame" value here (e.g., J2000)

	char calCode;

	static const unsigned int MAX_SRCNAME_LENGTH = 16;
};

std::ostream& operator << (std::ostream &os, const VexSource &x);

#endif
