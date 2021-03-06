#!/usr/bin/python
import argh
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from datetime import *
from os import path
from matplotlib.colors import ListedColormap

from plotting import ttp_style, add_grey

def multi_plot(reference_df, x_key, shade, saturate,
	colorlist=["0.9","#fff3a3","#a3e0ff","#ffa3ed","#ffa3a3"],
	padding=3,
	real_dates=True,
	window_start="",
	window_end="",
	save_plot=""
	):
	"""Plot a timetable

	Parameters
	----------

	reference_df : Pandas DataFrame
	Dataframe containing the data to plot. It needs to contain columns with datetime values.

	x_key : string
	Column from `reference_df` for the values in which to create rows in the timetable.

	shade: {list of str, list of dict}
	Strings specify the columns for which to shade the datetimes. In dictionaries, the key gives a column to filter by; and if the first item in the value list matches the column value, the datetime in the second item in the value list will specify which datetimes to shade; if the value list contains three items, the datetimes in between that in the second item column and the third item column will be shaded.

	saturate: {list of str, list of dict}
	Strings specify the columns for which to saturate the datetimes. In dictionaries, the key gives a column to filter by; and if the first item in the value list matches the column value, the datetime in the second item in the value list will specify which datetimes to saturate; if the value list contains three items, the datetimes in between that in the second item column and the third item column will be shaded.

	colorlist : list
	A list containing matplotlib-compatible colors to be used for shading.

	padding : int
	Number of days to bad the timetable window with (before and after the first and last scan respectively).

	real_dates : boolean
	Set to False to display dates relative to the first measurement.

	window_start : string
	A datetime-formatted string (e.g. "2016,12,18") to apply as the timetable start date (overrides autodetected start).

	window_end : string
	A datetime-formatted string (e.g. "2016,12,18") to apply as the timetable end date (overrides autodetected end).
	"""

	#truncate dates
	for col in reference_df.columns:
		if "date" in col:
			#the following catches None entries:
			try:
				reference_df[col] = reference_df[col].apply(lambda x: x.date())
			except AttributeError:
				pass

	#GET FIRST AND LAST DATE
	dates = get_dates(reference_df, [shade, saturate])
	if not window_start:
		window_start = min(dates) - timedelta(days=padding)
	else:
		window_start = datetime.strptime(window_start, "%Y,%m,%d").date()
	if not window_end:
		window_end = max(dates) + timedelta(days=padding)
	else:
		window_end = datetime.strptime(window_end, "%Y,%m,%d").date()

	#create generic plotting dataframe
	x_vals = list(set(reference_df[x_key]))
	datetime_index = [i for i in perdelta(window_start,window_end,timedelta(days=1))]

	df = pd.DataFrame(index=datetime_index, columns=x_vals)
	df = df.fillna(0)

	#set plotting params
	cMap = add_grey(cm.viridis, 0.9)
	fig_shape = (df.shape[0],df.shape[1]/1.5) #1.5 seems like a good scaling value to make cells not-too-tall and not-too-short
	fig, ax = plt.subplots(figsize=fig_shape , facecolor='#eeeeee', tight_layout=True)

	#populate frames
	df_ = df.copy(deep=True)
	for c_step, entry in enumerate(shade):
		c_step += 1
		for x_val in x_vals:
			if isinstance(entry, dict):
				for key in entry:
					start=False #unless the code below is succesful, no attempt is made to add an entry for the x_val
					filtered_df = reference_df[(reference_df[key] == entry[key][0])&(reference_df[x_key] == x_val)]
					try:
						start = list(set(filtered_df[entry[key][1]]))[0]
					except IndexError:
						pass
					if len(entry[key]) == 3:
						end = list(set(filtered_df[entry[key][2]]))[0]
						active_dates = [i for i in perdelta(start,end+timedelta(days=1),timedelta(days=1))]
						for active_date in active_dates:
							df_.set_value(active_date, x_val, df_.get_value(active_date, x_val)+c_step)
					elif start:
						df_.set_value(start, x_val, df_.get_value(start, x_val)+c_step)
			elif isinstance(entry, str):
				filtered_df = reference_df[reference_df[x_key] == x_val]
				active_dates = list(set(filtered_df[entry]))
				for active_date in active_dates:
					#escaping dates which are outside the date range (e.g. when specifying tighter window_end and window_start contraints)
					try:
						df_.set_value(active_date, x_val, df_.get_value(active_date, x_val)+c_step)
					except KeyError:
						pass
	if not real_dates:
		df_ = df_.set_index(np.arange(len(df_))-padding)
	im = ax.pcolorfast(df_.T, cmap=add_grey(cm.gray_r, 0.8), alpha=.5)
	plt.hold(True)

	#populate frames
	df_ = df.copy(deep=True)
	for c_step, entry in enumerate(saturate):
		c_step += 1
		for x_val in x_vals:
			if isinstance(entry, dict):
				for key in entry:
					filtered_df = reference_df[(reference_df[key] == entry[key][0])&(reference_df[x_key] == x_val)]
					try:
						start = list(set(filtered_df[entry[key][1]]))[0]
						try:
							start = start.date()
						except AttributeError:
							pass
					except IndexError:
						pass
					if len(entry[key]) == 3:
						try:
							end = list(set(filtered_df[entry[key][2]]))[0]
							active_dates = [i for i in perdelta(start,end+timedelta(days=1),timedelta(days=1))]
							for active_date in active_dates:
								df_.set_value(active_date, x_val, df_.get_value(active_date, x_val)+c_step)
						except IndexError:
							pass
					elif start:
						df_.set_value(start, x_val, df_.get_value(start, x_val)+c_step)
					# we need this to make sure start does not remain set for the next iteration:
					start=False
			elif isinstance(entry, str):
				filtered_df = reference_df[reference_df[x_key] == x_val]
				active_dates = list(set(filtered_df[entry]))
				df_.set_value(active_dates, x_val, 1)
	if not real_dates:
		df_ = df_.set_index(np.arange(len(df_))-padding)
	im = ax.pcolorfast(df_.T, cmap=ListedColormap(colorlist), vmin=0, vmax=len(colorlist)-1, alpha=.5)
	plt.hold(True)

	if real_dates:
		ax = ttp_style(ax, df_)
	else:
		ax = ttp_style(ax, df_, padding)
		plt.xlabel("Days")
	plt.ylabel(" ".join(x_key.split("_")).replace("id","ID"))

	if save_plot:
		plt.savefig(path.abspath(path.expanduser(save_plot)), bbox_inches='tight')

def perdelta(start, end, delta):
	curr = start
	while curr < end:
		yield curr
		curr += delta
	return

def get_dates(df, parameters):
	dates=[]
	for parameter in parameters:
		for entry in parameter:
			if isinstance(entry, str):
				notnull_df = df[pd.notnull(df[entry])]
				dates.extend(list(set(notnull_df[entry])))
			if isinstance(entry, dict):
				for key in entry:
					filtered_df = df[df[key] == entry[key][0]]
					for col in entry[key][1:]:
						dates.extend(list(set(filtered_df[col])))
	dates = list(set(dates))
	checked_dates=[]
	for dt in dates:
		try:
			checked_dates.append(dt.date())
		except AttributeError:
			checked_dates.append(dt)
	return checked_dates
