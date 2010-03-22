/***************************************************************************
 *   Copyright (C) 2006 by Adam Deller                                     *
 *                                                                         *
 *   This program is free for non-commercial use: see the license file     *
 *   at http://astronomy.swin.edu.au:~adeller/software/difx/ for more      *
 *   details.                                                              *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                  *
 ***************************************************************************/
#include "configuration.h"
#include <iomanip>
#include <sstream>

using namespace std;

int main(int argc, const char * argv[]) {
  Configuration * config;
  int freqindex;
  char polpair[3];
  string sourcename;
  ostringstream ss;

  polpair[2] = 0;

  if(argc != 2)
  {
    cerr << "Usage: difx_config <inputfile> " << endl;
    return EXIT_FAILURE;
  }

  config = new Configuration(argv[1], 0);

  int prod=0;
  for (int iconfig=0; iconfig<config->getNumConfigs(); iconfig++) {

    if (config->getNumConfigs()>1) {
      cout << endl << "*********** CONFIG " << iconfig << " ***********" << endl << endl;;
    }
    

    cout << "Number of channels " << config->getNumChannels(iconfig) << endl;
    cout << "Integration time  " << config->getIntTime(iconfig) << endl << endl;;

    int binloop = 1;
    if(config->pulsarBinOn(iconfig) && !config->scrunchOutputOn(iconfig))
      binloop = config->getNumPulsarBins(iconfig);

    for (int i=0;i<config->getNumBaselines();i++) {
      int ds1index = config->getBDataStream1Index(iconfig, i);
      int ds2index = config->getBDataStream2Index(iconfig, i);

      for(int j=0;j<config->getBNumFreqs(iconfig,i);j++) {
	freqindex = config->getBFreqIndex(iconfig, i, j);

	for(int b=0;b<binloop;b++) {
	  for(int k=0;k<config->getBNumPolProducts(iconfig, i, j);k++) {
	    config->getBPolPair(iconfig,i,j,k,polpair);
	    
	    cout << setw(3) << prod << ": ";

	    ss << config->getTelescopeName(ds1index) << "-" 
	       << config->getTelescopeName(ds2index);
	    cout << left << setw(15) << ss.str() << right;
	    ss.str("");

	    cout << " " << polpair << " ";

	    cout  << config->getFreqTableFreq(freqindex) << " MHz";
	    
	    cout << " (" << config->getFreqTableBandwidth(freqindex) << " MHz)";

	    cout << endl;
	    prod++;
	  }
	}
      }
    }

    int autocorrwidth = (config->getMaxProducts()>2)?2:1;
    
    for(int i=0;i<config->getNumDataStreams();i++) {
      for(int j=0;j<autocorrwidth;j++) {
	for(int k=0;k<config->getDNumOutputBands(iconfig, i); k++) {
	  
	  cout << setw(3) << prod << ": " << left << setw(15) 
	       << config->getDStationName(iconfig, i) << " " << right;
       
	  char firstpol = config->getDBandPol(iconfig, i, k);
	  char otherpol = ((firstpol == 'R')?'L':'R');
	  if (j==0)
	    cout << firstpol << firstpol;
	  else
	    cout << firstpol << otherpol;
	  
	  freqindex = config->getDFreqIndex(iconfig, i, k);
	  cout <<  " " << config->getFreqTableFreq(freqindex) << " MHz";
	  
	  cout << " (" << config->getFreqTableBandwidth(freqindex) << " MHz)";

	  cout << endl;
	  
	  prod++;
	}
      }
    }
  }
}

