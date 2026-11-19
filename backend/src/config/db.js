const mongoose = require('mongoose');
const env = require('./env');

let isConnected = false;

const connectDB = async () => {
  try {
    mongoose.set('strictQuery', false);
    const conn = await mongoose.connect(env.MONGODB_URI, {
      serverSelectionTimeoutMS: 3000,
      autoIndex: true,
    });
    isConnected = true;
    console.log(`[Database] MongoDB Connected: ${conn.connection.host}`);
    return conn;
  } catch (error) {
    isConnected = false;
    console.warn(`[Database] Standard MongoDB connection failed (${error.message}). Running in mock/memory-ready mode.`);
    return null;
  }
};

const getDbStatus = () => ({
  connected: mongoose.connection.readyState === 1 || isConnected,
  readyState: mongoose.connection.readyState,
  host: mongoose.connection.host || 'none',
  name: mongoose.connection.name || 'arkastra'
});

module.exports = { connectDB, getDbStatus };
