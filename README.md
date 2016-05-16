# TvShowWatch-2

## Introduction

TvShowWatch-2 will manage your TV Shows downloads by torrents.
You just indicate your favorite TV shows name and wait.

After that, TvShowWatch-2 can:
* Inform itself about the next broadcast
* Watch available torrent
* Push it to your torrent client
* Watch download progression
* Transfer completed downloads to your local storage
* Notify you
* Watch the next episode

## Dependencies
### Mandatory
* **Python2.7**
* **[Transmission] daemon** (plan to manage others or nothing for just download torrents)
* **pip** for automatic installation of python module dependencies

### Facultative
* [T411] account
* FTP/SFTP/Amazon/Swift server to transfer your completed downloads to/from
* [Synology] NAS with DSM 5.0 (package available)
* For synology setup, you need `python` package from [synoCommunity]
* Email account for notifications

## Setup
### Linux from source
* Download source (from [releases] or with git clone)
* Enter directory
* Type `make install` in order to download and install Dependencies
* Type `python tvShowWatch.py start` in order to launch web server and background process
* Go to `http://localhost:1205` to populate your configuration data
* In order to stop TvShowWatch-2, just type `python tvShowWatch stop`

### Synology DSM from 5.0
* Log into your NAS as administrator and go to **Main Menu** → **Package Center** → **Settings** and set Trust Level to *Any editor*.
* In the **Package Sources** tab, click **Add**, type *SynoCommunity* as **Name** and *http://packages.synocommunity.com/* as **Location** and then press **OK** to validate.
* Go back to the **Package Center** and install SynoCommunity's **python** (not ~~python3~~)package in the **Community** tab.
* Download TvShowWatch-2.spk package file from [releases]
* In **Package Center**, click **Manual Install** and enter the TvShowWatch2.spk file.
* Run the package and go to `http://your_synology_url:1205` to populate your configuration data


[SynoCommunity]: https://synocommunity.com/
[T411]: https://t411.ch
[Synology]: http://www.synology.com
[releases]: https://github.com/kavod/TvShowWatch-2/releases
[Transmission]: https://www.transmissionbt.com/download/
