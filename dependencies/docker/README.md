# Build Image Martin Vector tile server

This is a document martin for the Martin Vector Tile Server. It is based on
the [official martin image](https://maplibre.org/martin/installation.html).

## Configuration martin server

***You can edit configuration from location at dependencies/dockerfile/config.yaml***

```yaml
# Connection keep alive timeout [default: 75]
keep_alive: 75

# The socket address to bind [default: 0.0.0.0:3000]
listen_addresses: '0.0.0.0:3000'

# Number of web server workers
worker_processes: 8

# Amount of memory (in MB) to use for caching tiles [default: 512, 0 to disable]
cache_size_mb: 1024

# Database configuration. This can also be a list of PG configs.
postgres:
  # Database connection string. You can use env vars too, for example:
  #   $DATABASE_URL
  #   ${DATABASE_URL:-postgresql://postgres@localhost/db}
  # Example url with user and password:
  # postgresql://postgres:-nndKn7M78s_LVkYr0aWGsbG^vL^w4@eoapi-db-sp-v1p2-rds-db.ckyrwixtzept.ap-southeast-1.rds.amazonaws.com:5432/postgres
  connection_string: '<<POSTGRES_CONNECTION_STRING>>'

  # Same as PGSSLCERT for psql
  # ssl_cert: './postgresql.crt'
  # Same as PGSSLKEY for psql
  # ssl_key: './postgresql.key'
  # Same as PGSSLROOTCERT for psql
  # ssl_root_cert: './root.crt'

  #  If a spatial table has SRID 0, then this SRID will be used as a fallback
  default_srid: 4326

  # Maximum Postgres connections pool size [default: 20]
  pool_size: 20

  # Limit the number of table geo features included in a tile. Unlimited by default.
  max_feature_count: 1000

  # Control the automatic generation of bounds for spatial tables [default: quick]
  # 'calc' - compute table geometry bounds on startup.
  # 'quick' - same as 'calc', but the calculation will be aborted if it takes more than 5 seconds.
  # 'skip' - do not compute table geometry bounds on startup.
  auto_bounds: skip

  # Enable automatic discovery of tables and functions.
  # You may set this to `false` to disable.
  auto_publish:
    # Optionally limit to just these schemas
    from_schemas:
      - landuse
    # Here we enable both tables and functions auto discovery.
    # You can also enable just one of them by not mentioning the other,
    # or setting it to false.  Setting one to true disables the other one as well.
    # E.g. `tables: false` enables just the functions auto-discovery.
    tables:
      # Optionally set how source ID should be generated based on the table's name, schema, and geometry column
      source_id_format: '{table}'
      # Add more schemas to the ones listed above
      from_schemas: landuse
      # A table column to use as the feature ID
      # If a table has no column with this name, `id_column` will not be set for that table.
      # If a list of strings is given, the first found column will be treated as a feature ID.
      id_columns: feature_id
      # Boolean to control if geometries should be clipped or encoded as is, optional, default to true
      clip_geom: true
      # Buffer distance in tile coordinate space to optionally clip geometries, optional, default to 64
      buffer: 64
      # Tile extent in tile coordinate space, optional, default to 4096
      extent: 4096
    functions:
      # Optionally set how source ID should be generated based on the function's name and schema
      source_id_format: '{function}'


    # Associative arrays of table sources
    #  tables:
    #    data_sources:
    #      # ID of the MVT layer (optional, defaults to table name)
    #      layer_id: data_sources
    #
    #      # Table schema (required)
    #      schema: landuse
    #
    #      # Table name (required)
    #      table: data_sources
    #
    #      # Geometry SRID (required)
    #      srid: 4326
    #
    #      # Geometry column name (required)
    #      geometry_column: geometry
    #
    #      # Feature id column name
    #      id_column: ~
    #
    #      # An integer specifying the minimum zoom level
    #      minzoom: 0
    #
    #      # An integer specifying the maximum zoom level. MUST be >= minzoom
    #      maxzoom: 30
    #
    #      # The maximum extent of available map tiles. Bounds MUST define an area
    #      # covered by all zoom levels. The bounds are represented in WGS:84
    #      # latitude and longitude values, in the order left, bottom, right, top.
    #      # Values may be integers or floating point numbers.
    #      bounds: [-180.0, -90.0, 180.0, 90.0]
    #
    #      # Tile extent in tile coordinate space
    #      extent: 4096
    #
    #      # Buffer distance in tile coordinate space to optionally clip geometries
    #      buffer: 64
    #
    #      # Boolean to control if geometries should be clipped or encoded as is
    #      clip_geom: true
    #
    #      # Geometry type
    #      geometry_type: GEOMETRY
    #
    #      # List of columns, that should be encoded as tile properties (required)
    #      properties:
    #        gid: int4

    # Associative arrays of function sources
    #  functions:
    #    fn_data_sources:
    #      # Schema name (required)
    #      schema: landuse
    #
    #      # Function name (required)
    #      function: fn_data_sources
    #
    #
    #      # An integer specifying the minimum zoom level
    #      minzoom: 0
    #
    #      # An integer specifying the maximum zoom level. MUST be >= minzoom
    #      maxzoom: 30
    #
    #      # The maximum extent of available map tiles. Bounds MUST define an area
    #      # covered by all zoom levels. The bounds are represented in WGS:84
    #      # latitude and longitude values, in the order left, bottom, right, top.
    #      # Values may be integers or floating point numbers.
    #      bounds: [-180.0, -90.0, 180.0, 90.0]

    # Publish PMTiles files from local disk or proxy to a web server
    # pmtiles:
    #   paths:
    #     # scan this whole dir, matching all *.pmtiles files
    #     - /dir-path
    #     # specific pmtiles file will be published as a pmt source (filename without extension)
    #     - /path/to/pmt.pmtiles
    #     # A web server with a PMTiles file that supports range requests
    #     - https://example.org/path/tiles.pmtiles
    #   sources:
    #     # named source matching source name to a single file
    #     pm-src1: /path/to/pmt.pmtiles
    #     # A named source to a web server with a PMTiles file that supports range requests
    #     pm-web2: https://example.org/path/tiles.pmtiles

# # Publish MBTiles files
# mbtiles:
#   paths:
#     # scan this whole dir, matching all *.mbtiles files
#     - /dir-path
#     # specific mbtiles file will be published as mbtiles2 source
#     - /path/to/mbtiles.mbtiles
#   sources:
#     # named source matching source name to a single file
#     mb-src1: /path/to/mbtiles1.mbtiles

# # Sprite configuration
# sprites:
#   paths:
#     # all SVG files in this dir will be published as a "my_images" sprite source
#     - /path/to/my_images
#   sources:
#     # SVG images in this directory will be published as a "my_sprites" sprite source
#     my_sprites: /path/to/some_dir

# # Font configuration
# fonts:
#   # A list of *.otf, *.ttf, and *.ttc font files and dirs to search recursively.
#   - /path/to/font/file.ttf
#   - /path/to/font_dir

```

## Usage

To build the image, run the following command:

```bash

docker build -t martin-vector-tile-server .
docker run -d -p 3000:3000 martin-vector-tile-server

```

Or install the martin server with native installation:

```bash

brew tap maplibre/martin
brew install martin

```