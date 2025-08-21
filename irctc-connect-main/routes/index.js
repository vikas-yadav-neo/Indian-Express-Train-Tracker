import express from "express";
import {
  checkPNRStatus,
  getTrainInfo,
  liveAtStation,
  searchTrainBetweenStations,
  trackTrain,
} from "../controller/train.controller.js";

const router = express.Router();
router.get("/trainInfo", getTrainInfo);
router.get("/checkPNRStatus", checkPNRStatus);
router.post("/trackTrain", trackTrain);
router.get("/liveAtStation", liveAtStation);
router.post("/searchTrainBetweenStations", searchTrainBetweenStations);

export default router;
