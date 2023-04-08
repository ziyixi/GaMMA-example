import json
from datetime import datetime

import numpy as np
import pandas as pd
from gamma.utils import association
from pyproj import Proj

def main():
    # * configs
    config = {
        "center": (-178, -19),
        "xlim_degree": [170, -166],
        "ylim_degree": [-31, -7],
    }

    # setting GMMA configs
    config["use_amplitude"] = False
    config["method"] = "BGMM"
    config["oversample_factor"] = 8

    # earthquake location
    # config["vel"] = {"p": 6.0, "s": 6.0 / 1.75}
    config["dims"] = ['x(km)', 'y(km)', 'z(km)']
    proj = Proj(
        f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
    xd = proj(longitude=config["xlim_degree"][0],
            latitude=config["ylim_degree"][0])
    yd = proj(longitude=config["xlim_degree"][1],
            latitude=config["ylim_degree"][1])
    config["x(km)"] = [xd[0], yd[0]]  # pylint: disable=unsubscriptable-object
    config["y(km)"] = [xd[1], yd[1]]  # pylint: disable=unsubscriptable-object
    config["z(km)"] = (0, 700)
    config["bfgs_bounds"] = (
        (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
        (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
        (10, config["z(km)"][1] + 1),  # z
        (None, None),  # t
    )

    # DBSCAN
    config["use_dbscan"] = True
    config["dbscan_eps"] = 300
    config["dbscan_min_samples"] = 3

    # filtering
    config["min_picks_per_eq"] = 3
    config["min_p_picks_per_eq"] = 0
    config["min_s_picks_per_eq"] = 0
    config["max_sigma11"] = 1000.0  # s
    config["max_sigma22"] = 1000.0  # log10(m/s)
    config["max_sigma12"] = 1000.0  # covariance

    config["starttime"] = datetime(2009, 12, 1, 0, 0)
    config["endtime"] = datetime(2011, 1, 1, 0, 0)
    config["initial_points"]=[1,1,1]

    # Eikonal for 1D velocity model
    d, Vpv, Vph, Vsv, Vsh = np.loadtxt(
        './data/PREM.csv', usecols=(1, 3, 4, 5, 6), unpack=True, skiprows=1, delimiter=",")
    Vp = np.sqrt((Vpv**2 + 4 * Vph**2)/5)
    Vs = np.sqrt((2 * Vsv**2 + Vsh**2)/3)
    vel = {"z": d, "p": Vp, "s": Vs}
    config["eikonal"] = {"vel": vel, "h": 1,
                        "xlim": config["x(km)"], "ylim": config["y(km)"], "zlim": config["z(km)"]}
    config["covariance_prior"] = [120, 120]

    # config["ncpu"]=1

    # * prepare stations
    stations_mapper = {}

    with open("./data/stations.json") as json_file:
        stations_raw = json.load(json_file)
    stations = pd.DataFrame(columns=["id", "x(km)", "y(km)", "z(km)"])
    proj = Proj(
        f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
    for key in stations_raw:
        row = stations_raw[key]
        x, y = proj(longitude=row["longitude"], latitude=row["latitude"]) # pylint: disable=unpacking-non-sequence
        z = -row["elevation_m"]/1000
        stations.loc[len(stations)] = [key, x, y, z]
        stations_mapper[key.split(".")[1]] = key

    # * prepare picks
    picks_raw = pd.read_csv("./data/phase_picks.csv",comment="#")
    picks = pd.DataFrame(
        columns=["event_id", "id", "timestamp", "amp", "type", "prob"])
    for i in range(len(picks_raw)):
        row = picks_raw.iloc[i]
        phase_type = row.phase_type
        if phase_type == "P":
            phase_type = "p"
        elif phase_type == "S":
            phase_type = "s"
        else:
            continue
        picks.loc[len(picks)] = [
            row.event_id, stations_mapper[row.station_id], row.phase_time[:-1], 1e-6, phase_type, 1.0]

    # * do association

    event_idx0 = 0
    assignments = []
    catalogs, assignments = association(
        picks, stations, config, event_idx0, config["method"])
    event_idx0 += len(catalogs)

    # * create catalog
    catalogs_pd = pd.DataFrame(catalogs, columns=["time"]+config["dims"]+[
                            "magnitude", "sigma_time", "sigma_amp", "cov_time_amp",  "event_index", "gamma_score"])
    catalogs_pd[["longitude", "latitude"]] = catalogs_pd.apply(lambda x: pd.Series(
        proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)), axis=1)
    catalogs_pd["depth(m)"] = catalogs_pd["z(km)"].apply(lambda x: x*1e3)
    catalogs_pd.to_csv("./res/catalogs.csv", sep="\t")

    assignments_pd = pd.DataFrame(
        assignments, columns=["pick_index", "event_index", "gamma_score"])
    picks_test_pd = picks.join(assignments_pd.set_index(
        "pick_index")).fillna(-1).astype({'event_index': int})
    picks_test_pd.to_csv(
        "./res/picks.csv", sep="\t")

if __name__ == "__main__":
    main()