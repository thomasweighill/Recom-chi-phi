# Recom-chi-phi
These are some scripts for generating ensembles of districting plans for Chicago and Philadelphia.
To run an ensemble of 10000 50-district plans for Chicago, you can go:
`python -u recom_Chicago_Philly 10000 1 output 50 Chicago`
More generally, you can run
`python -u recom_Chicago_Philly [steps] [sampling interval] [output folder] [number of districts] [city]`
where city can be Chicago, Philly or Phillyblocks.
