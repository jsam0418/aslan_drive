# Aslan Drive: Algo/Quant trading infrastructure  

## Project Goals
1. A generic backtesting environment that would allow for the study and research into trade strategies and signals.
2. A relational timeseries database that contains historical data for various instruments and asset types
3. A metadata database that tracks supplemental information about different assets and classes.
4. A data loading infrastructure that pulls the most recent day's data and loads it into the database.
5. Database backups.
6. Monitoring and reporting. 

## Project Design Doc

There are a few components to this project. 

1. Historical Data loaders
    - These are "One Off" loaders that can load raw files into the database
    - Since the database format might be changing often, these loaders will need to be kept around to reload data.
2. Live Data loaders
    - The live data loaders will subscribe to a feed and get the data for the preivous trade date. 
    - Its possible the live data provider will not be the same as the historical data provider.
3. Database
    - The database will have two components
        - Timeseries Database: This will hold the historical tick data that was purchased from vendors
        - Metadata Database: This will hold the suplemental information about each symbol/class/vendor/strategy/etc.
    - The database will need to be backed up weekly in order to provide data recovery options in case of a failure.
4. MD Provider
    - This "layer" provides access to the data in the two components of the database.
    - This layer is needed since the database may be changing often, we want to isolate those changes to the provider.
    - This layer could be as simple as a rest api
5. Backtest environment
    - This will most likely be zipline, but with a custom data ingestion pipeline to load from our DB
    - With the MD Provider API, it will be easy to configure different test sets
