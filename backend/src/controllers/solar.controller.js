const dataStore = require('../services/dataStore');

exports.getObservations = async (req, res) => {
  try {
    const page = parseInt(req.query.page, 10) || 1;
    const limit = parseInt(req.query.limit, 10) || 50;
    const observations = await dataStore.getRecentObservations(limit * page);
    const paginated = observations.slice((page - 1) * limit, page * limit);

    res.json({
      success: true,
      page,
      limit,
      total: observations.length,
      observations: paginated,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getFlux = async (req, res) => {
  try {
    const limit = parseInt(req.query.limit, 10) || 100;
    const fluxData = await dataStore.getRecentObservations(limit);
    res.json({
      success: true,
      count: fluxData.length,
      data: fluxData,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getEvents = async (req, res) => {
  try {
    const limit = parseInt(req.query.limit, 10) || 50;
    const classFilter = req.query.flareClass ? req.query.flareClass.toUpperCase() : null;
    let events = await dataStore.getRecentEvents(limit * 2);

    if (classFilter) {
      events = events.filter((e) => e.classCategory === classFilter);
    }

    res.json({
      success: true,
      count: events.slice(0, limit).length,
      events: events.slice(0, limit),
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};
