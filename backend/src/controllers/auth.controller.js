const jwt = require('jsonwebtoken');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const User = require('../models/User');
const env = require('../config/env');

const generateToken = (id) => {
  return jwt.sign({ id }, env.JWT_SECRET, { expiresIn: '30d' });
};

// In-memory fallback users when Mongo is disconnected
const memoryUsers = [];
const isDbActive = () => mongoose.connection.readyState === 1;

exports.register = async (req, res) => {
  const { name, email, password, role } = req.body;
  if (!email || !password || !name) {
    return res.status(400).json({ success: false, message: 'Please provide all required fields' });
  }

  if (isDbActive()) {
    try {
      const userExists = await User.findOne({ email });
      if (userExists) {
        return res.status(400).json({ success: false, message: 'User already exists' });
      }

      const user = await User.create({
        name,
        email,
        password,
        role: role || 'researcher',
      });

      return res.status(201).json({
        success: true,
        user: {
          id: user._id,
          name: user.name,
          email: user.email,
          role: user.role,
        },
        token: generateToken(user._id),
      });
    } catch (err) {
      console.warn('[Auth] Mongoose create failed, falling back to memory store.');
    }
  }

  // Memory fallback
  const existing = memoryUsers.find((u) => u.email === email);
  if (existing) {
    return res.status(400).json({ success: false, message: 'User already exists' });
  }
  const id = `mem_user_${Date.now()}`;
  const salt = await bcrypt.genSalt(10);
  const hashedPassword = await bcrypt.hash(password, salt);
  const user = { id, name, email, role: role || 'researcher', password: hashedPassword };
  memoryUsers.push(user);

  res.status(201).json({
    success: true,
    user: { id, name, email, role: user.role },
    token: generateToken(id),
    mode: 'memory_session',
  });
};

exports.login = async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) {
    return res.status(400).json({ success: false, message: 'Please provide email and password' });
  }

  if (isDbActive()) {
    try {
      const user = await User.findOne({ email });
      if (user && (await user.matchPassword(password))) {
        return res.json({
          success: true,
          user: {
            id: user._id,
            name: user.name,
            email: user.email,
            role: user.role,
          },
          token: generateToken(user._id),
        });
      }
      return res.status(401).json({ success: false, message: 'Invalid credentials' });
    } catch (err) {
      console.warn('[Auth] Mongoose login query failed, falling back to memory store.');
    }
  }

  // Memory fallback
  const memUser = memoryUsers.find((u) => u.email === email);
  if (memUser) {
    const isMatch = await bcrypt.compare(password, memUser.password);
    if (isMatch) {
      return res.json({
        success: true,
        user: {
          id: memUser.id,
          name: memUser.name,
          email: memUser.email,
          role: memUser.role,
        },
        token: generateToken(memUser.id),
      });
    }
  }
  return res.status(401).json({ success: false, message: 'Invalid credentials' });
};

exports.getMe = async (req, res) => {
  if (req.user) {
    return res.json({ success: true, user: req.user });
  }
  res.json({
    success: true,
    user: {
      name: 'Guest Space Observer',
      role: 'observer',
      authenticated: false,
    },
  });
};
