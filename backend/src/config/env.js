require('dotenv').config();
const { z } = require('zod');

const envSchema = z.object({
  PORT: z.string().default('5000'),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  MONGODB_URI: z.string().default('mongodb://localhost:27017/arkastra'),
  JWT_SECRET: z.string().default('arkastra_secret_key_solar_flare_forecaster_2026'),
  ML_SERVICE_URL: z.string().default('http://localhost:8000'),
  NOAA_BASE_URL: z.string().default('https://services.swpc.noaa.gov'),
  NASA_DONKI_API_KEY: z.string().default('DEMO_KEY'),
  CORS_ORIGIN: z.string().default('http://localhost:5173'),
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error('Invalid environment variables:', parsed.error.format());
  process.exit(1);
}

module.exports = parsed.data;
