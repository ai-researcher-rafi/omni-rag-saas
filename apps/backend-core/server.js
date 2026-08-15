const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const connectDB = require('./src/config/db');

dotenv.config();
connectDB();

const app = express();

app.use(express.json());
app.use(cors());

// Health Check Route
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', message: 'backend-core system is running fine!' });
});

// API Routes
app.use('/api/v1/auth', require('./src/routes/authRoutes'));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`[Server] Core Backend running on port ${PORT}`);
});