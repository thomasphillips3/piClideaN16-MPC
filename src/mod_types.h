/* E01: bounded per-instance modulation. No allocation or device work here. */
#define MOD_SLOTS 4
#define MOD_FIELDS 18
#define MOD_PER_LANE (1+2*MOD_FIELDS)
#define MOD_PARAMS ((LANES+1)*MOD_PER_LANE)
#define MOD_DEST_NOTE 7
#define MOD_VIS_COUNT (LANES+5+64)
typedef struct { int f[MOD_FIELDS]; } ModOsc;
typedef struct { ModOsc osc[2]; int mix; } ModLane;
