from rasterstats import zonal_stats
import click
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sdt.changepoint
# parcels_csv = "grazing/AOIs/2022_parcels.csv"
# parcels_shapefile = 'grazing/AOIs/2022_parcels.shp'
# imagery_path = 'grazing/2022_s1'
# CD_sensitivity = 0.0001
# out_csv = "grazing/parcels/final_2022_grazing.csv"
def grazing (parcels_csv, parcels_shapefile, imagery_path, CD_sensitivity, out_csv):
    parcelscsv = pd.read_csv(parcels_csv)
    pathdir = imagery_path
    VV_stats = np.zeros((len(os.listdir(pathdir)),len(parcelscsv['FOI_ID'])))
    for i in range(len(os.listdir(pathdir))):
        VV = pd.DataFrame(zonal_stats(parcels_shapefile, os.path.join(pathdir, os.listdir(pathdir)[i]), stats='mean', band=2))
        VV_stats[i] = VV['mean']
    np.savetxt("grazing/VVstats.txt", VV_stats)

    VV_stats = np.loadtxt("grazing/VVstats.txt")
    dates = []
    for i in range(len(os.listdir(pathdir))):
        dates+=[os.listdir(pathdir)[i][28:-25]]
    dates = sorted(dates)
    field_IDs = parcelscsv['FOI_ID']
    temporal_means_VV = pd.DataFrame(VV_stats, columns=field_IDs, index=dates)
    temporal_means_VV.to_csv('grazing/temporal_meansVV_2022.csv')

    dates_words = ['08-05-2022  00:00:00', '20-05-2022  00:00:00', '01-06-2022  00:00:00', '13-06-2022  00:00:00', '25-06-2022  00:00:00', '07-07-2022  00:00:00', '31-07-2022  00:00:00', '12-08-2022  00:00:00', '24-08-2022  00:00:00', '05-09-2022  00:00:00', '17-09-2022  00:00:00', '29-09-2022  00:00:00']
    columnss = ['EVT_ID', 'EVT_FOI_ID',	'EVT_ALGORITHM','EVT_ALGORITHM_VERSION', 'EVT_ANALYSIS_START_DATE',	'EVT_ANALYSIS_END_DATE', 'EVT_DATE_LAST_SIGNAL', 'EVT_TREND', 'EVT_INTERPRETATION', 'EVT_EVENT_START_DATE',	'EVT_EVENT_END_DATE', 'EVT_PROBABILITY', 'REASON_NO_RESULT']
    final_df = pd.DataFrame(columns=columnss)
    final_df['EVT_ID'] = np.arange(len(field_IDs))
    final_df['EVT_FOI_ID'] = field_IDs
    final_df['EVT_ALGORITHM'] = 'grazing_detection_marker'
    final_df['EVT_ALGORITHM_VERSION'] = '0.0.1'
    final_df['EVT_ANALYSIS_START_DATE'] = '08-05-2022'
    final_df['EVT_ANALYSIS_END_DATE'] = '29-09-2022'
    final_df['EVT_DATE_LAST_SIGNAL'] = '01-01-1900  00:00:00'
    for i in range(len(field_IDs)):
        field = field_IDs[i]
        det = sdt.changepoint.Pelt(min_size=0, jump=1)
        data = np.array(temporal_means_VV[field])
        changes = det.find_changepoints(data, CD_sensitivity)
        # plt.figure(figsize=(15, 7))
        # plt.title(f'Change Point Detection: Pelt Search Method. Field ID {field}. Number of changes {len(changes)}.')
        # plt.ylim(0, 0.51)
        # plt.plot(temporal_means_VV.index, data, c='k', label='VV Coherence')
        # plt.vlines(temporal_means_VV.index[changes], 0, 0.6, colors='r', label='Changes VV')
        # plt.ylabel('Coherence [-]')
        # plt.xlabel('Date [mmdd]')
        # plt.legend()
        change_dates = []
        grazing_dates=[]
        j = 0
        the_change = list(np.empty(len(changes), dtype='str'))
        for j in range(len(changes)):
            change_dates += [dates[changes[j]]]
            if data[changes[j]] > data[changes[j] - 1]:
                the_change[j] = 'Grazing'
                grazing_dates += [dates_words[changes[j]]]
            elif data[changes[j]] < data[changes[j] - 1]:
                the_change[j] = 'No grazing'
        if len(grazing_dates) == 1:
            final_df.at[i, 'EVT_TREND'] = 'Grazing'
            final_df.at[i, 'EVT_INTERPRETATION'] = 'Grazing'
            final_df.at[i, 'EVT_EVENT_START_DATE'] = grazing_dates[0]
            final_df.at[i, 'EVT_EVENT_END_DATE'] = grazing_dates[0]
        elif len(grazing_dates) >= 2:
            final_df.at[i, 'EVT_TREND'] = 'Grazing'
            final_df.at[i, 'EVT_INTERPRETATION'] = 'Grazing'
            final_df.at[i, 'EVT_EVENT_START_DATE'] = grazing_dates[0]
            final_df.at[i, 'EVT_EVENT_END_DATE'] = grazing_dates[-1]
        elif len(grazing_dates) == 0:
            final_df.at[i, 'REASON_NO_RESULT'] = 'No detection'

    final_df.to_csv(out_csv, index=False)
    return final_df.count()

@click.command()
@click.argument('parcels_csv', type=click.Path(exists=True))
@click.argument('parcels_shapefile', type=click.Path(exists=True))
@click.argument('imagery_path', type=click.Path(exists=True))
@click.argument('CD_sensitivity', type=float)
@click.argument('out_csv', type=click.Path())
def init(parcels_csv, parcels_shapefile, imagery_path, CD_sensitivity, out_csv):
    """
    FINT is an input filepath

    FOUT is an output filepath
    """
    grazing(parcels_csv, parcels_shapefile, imagery_path, CD_sensitivity, out_csv)


if __name__ == "__main__":
    init()

