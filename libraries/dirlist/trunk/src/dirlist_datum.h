#ifndef __DIRLIST_DATUM_H__
#define __DIRLIST_DATUM_H__

#include <string>
#include <ostream>

// corresponds to a single scan;
class DirListDatum
{
public:
	DirListDatum() : mjdStart(0), secStart(0.0), duration(0.0) {}
	virtual ~DirListDatum() {}
	const std::string &getName() const { return name; }
	int getMjdStart() const { return mjdStart; }
	double getSecStart() const { return secStart; }
	double getDuration() const { return duration; }
	void setName(const std::string &n) { name = n; }
	void setMjdStart(int mjd) { mjdStart = mjd; }
	void setSecStart(double sec) { secStart = sec; }
	void setStart(int mjd, double sec) { mjdStart = mjd; secStart = sec; }
	void setDuration(double dur) { duration = dur; }
	virtual void print(std::ostream &os, bool doEOL = true) const;
	void printComment(std::ostream &os, bool doEOL = true) const;
	bool hasComment() const { return !comment.empty(); }
	void setComment(const std::string &str) { comment = str; }

protected:
	// start time in MJD = mjdStart + secStart/86400.0
	int mjdStart;
	double secStart;
	double duration;
	std::string name;		// name of file or scan
	std::string comment;
};

std::ostream& operator << (std::ostream &os, const DirListDatum &x);

#endif
