@echo off

set rimWorldPath=G:\Steam\steamapps\common\RimWorld

mkdir .Data

mkdir .Data\Core
mklink /J .Data\Core\Defs %rimWorldPath%\Data\Core\Defs
mklink /J .Data\Core\Keyed %rimWorldPath%\Data\Core\Languages\English\Keyed
mklink /J .Data\Core\Strings %rimWorldPath%\Data\Core\Languages\English\Strings

mkdir .Data\Royalty
mklink /J .Data\Royalty\Defs %rimWorldPath%\Data\Royalty\Defs
mklink /J .Data\Royalty\Keyed %rimWorldPath%\Data\Royalty\Languages\English\Keyed
mklink /J .Data\Royalty\Strings %rimWorldPath%\Data\Royalty\Languages\English\Strings

mkdir .Data\Ideology
mklink /J .Data\Ideology\Defs %rimWorldPath%\Data\Ideology\Defs
mklink /J .Data\Ideology\Keyed %rimWorldPath%\Data\Ideology\Languages\English\Keyed

mkdir .Data\Biotech
mklink /J .Data\Biotech\Defs %rimWorldPath%\Data\Biotech\Defs
mklink /J .Data\Biotech\Keyed %rimWorldPath%\Data\Biotech\Languages\English\Keyed
mklink /J .Data\Biotech\Strings %rimWorldPath%\Data\Biotech\Languages\English\Strings

mkdir .Data\Anomaly
mklink /J .Data\Anomaly\Defs %rimWorldPath%\Data\Anomaly\Defs
mklink /J .Data\Anomaly\Keyed %rimWorldPath%\Data\Anomaly\Languages\English\Keyed
mklink /J .Data\Anomaly\Strings %rimWorldPath%\Data\Anomaly\Languages\English\Strings

mkdir .Data\Odyssey
mklink /J .Data\Odyssey\Defs %rimWorldPath%\Data\Odyssey\Defs
mklink /J .Data\Odyssey\Keyed %rimWorldPath%\Data\Odyssey\Languages\English\Keyed
