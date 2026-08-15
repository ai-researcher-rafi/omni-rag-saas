const Tenant = require('../models/Tenant');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

// Tenant Registration
exports.registerTenant = async (req, res) => {
  try {
    const { companyName, email, password } = req.body;

    let tenantExists = await Tenant.findOne({ email });
    if (tenantExists) {
      return res.status(400).json({ message: 'Tenant email already registered.' });
    }

    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    
    // Unique Tenant ID generation
    const tenantId = `tenant_${Date.now()}`;

    const tenant = await Tenant.create({
      companyName,
      email,
      password: hashedPassword,
      tenantId
    });

    res.status(201).json({
      success: true,
      message: 'Tenant registered successfully!',
      tenantId: tenant.tenantId
    });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
};

// Tenant Login
exports.loginTenant = async (req, res) => {
  try {
    const { email, password } = req.body;

    const tenant = await Tenant.findOne({ email });
    if (!tenant) {
      return res.status(400).json({ message: 'Invalid credentials.' });
    }

    const isMatch = await bcrypt.compare(password, tenant.password);
    if (!isMatch) {
      return res.status(400).json({ message: 'Invalid credentials.' });
    }

    const token = jwt.sign(
      { id: tenant._id, tenantId: tenant.tenantId },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.status(200).json({
      success: true,
      token,
      tenant: {
        id: tenant._id,
        companyName: tenant.companyName,
        tenantId: tenant.tenantId
      }
    });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
};