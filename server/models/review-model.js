const mongoose = require("mongoose");

// Problem-Solution Schema
const problemSolutionSchema = new mongoose.Schema({
  problem: {
    type: String,
    required: true,  // Ensure problem is a required field
  },
  solution: {
    type: String,
    required: true,  // Ensure solution is a required field
  },
});

// Create the model
const ProblemSolution = mongoose.model("ProblemSolution", problemSolutionSchema);

module.exports = ProblemSolution;
