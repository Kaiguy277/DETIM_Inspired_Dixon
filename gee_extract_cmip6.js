/*
 * Extract NEX-GDDP-CMIP6 daily temperature and precipitation
 * for Dixon Glacier (59.66°N, 150.88°W), 2025–2100.
 *
 * Paste this into https://code.earthengine.google.com/ and click Run.
 * Exports will appear in your Tasks tab — click Run on each one.
 * CSVs will be saved to your Google Drive in a folder called
 * "dixon_cmip6".
 *
 * 5 GCMs × 3 SSPs = 15 export tasks.
 * Each CSV has columns: date, temperature (C), precipitation (mm/day)
 */

var point = ee.Geometry.Point([-150.88, 59.66]);

var gcms = [
  'ACCESS-CM2',
  'EC-Earth3',
  'MPI-ESM1-2-HR',
  'MRI-ESM2-0',
  'NorESM2-MM'
];

var scenarios = ['ssp126', 'ssp245', 'ssp585'];

var startDate = '2025-01-01';
var endDate   = '2100-12-31';

// Load the full collection once
var nex = ee.ImageCollection('NASA/GDDP-CMIP6');

gcms.forEach(function(gcm) {
  scenarios.forEach(function(ssp) {

    var filtered = nex
      .filter(ee.Filter.eq('model', gcm))
      .filter(ee.Filter.eq('scenario', ssp))
      .filterDate(startDate, endDate)
      .select(['tas', 'pr']);

    // Extract the pixel values as a FeatureCollection
    var extracted = filtered.map(function(image) {
      var vals = image.reduceRegion({
        reducer: ee.Reducer.first(),
        geometry: point,
        scale: 27830  // native resolution ~0.25 deg
      });

      // Convert: tas from K to C, pr from kg/m2/s to mm/day
      var tasC = ee.Number(vals.get('tas')).subtract(273.15);
      var prMM = ee.Number(vals.get('pr')).multiply(86400);

      return ee.Feature(null, {
        'date': image.date().format('YYYY-MM-dd'),
        'temperature': tasC,
        'precipitation': prMM
      });
    });

    // Export to Drive
    var taskName = 'dixon_' + gcm + '_' + ssp;
    Export.table.toDrive({
      collection: extracted,
      description: taskName,
      folder: 'dixon_cmip6',
      fileNamePrefix: taskName,
      fileFormat: 'CSV',
      selectors: ['date', 'temperature', 'precipitation']
    });

    print('Queued: ' + taskName + ' (' + ssp + ')');
  });
});

print('All 15 exports queued. Go to Tasks tab and click Run on each.');
