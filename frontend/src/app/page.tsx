"use client";

import React, { useState } from "react";
import { CyberHUDNav } from "@/components/CyberHUDNav";
import { AIIntelligenceHUD } from "@/components/AIIntelligenceHUD";
import { HeroExperience } from "@/components/HeroExperience";
import { DemoJourneyController, DEMO_STEPS } from "@/components/DemoJourneyController";
import { IntelligentAnatomyLab } from "@/components/IntelligentAnatomyLab";
import { AITutorStudio } from "@/components/AITutorStudio";
import { ClinicalMCQEngine } from "@/components/ClinicalMCQEngine";
import { CaseSimulationRoom } from "@/components/CaseSimulationRoom";
import { StudentCommandCenter } from "@/components/StudentCommandCenter";
import { InstitutionAdminView } from "@/components/InstitutionAdminView";
import { InvestorPitchView } from "@/components/InvestorPitchView";
import { HackathonDeepDiveModal } from "@/components/HackathonDeepDiveModal";

import { INITIAL_STUDENT_PROFILE } from "@/lib/demo-data";
import { NavigationMode, StudentMasteryProfile, UserRole } from "@/lib/types";

// Modes where the evidence status bar is contextually relevant
const EVIDENCE_HUD_MODES: NavigationMode[] = ["tutor", "quiz", "simulation", "anatomy"];

export default function Home() {
  const [currentMode, setCurrentMode] = useState<NavigationMode>("landing");
  const [userRole, setUserRole] = useState<UserRole>("STUDENT");

  // Demo Journey State
  const [isDemoActive, setIsDemoActive] = useState(false);
  const [demoStepIdx, setDemoStepIdx] = useState(0);

  // Pipeline Deep Dive Modal State
  const [isPipelineModalOpen, setIsPipelineModalOpen] = useState(false);

  // Cross-component parameters
  const [tutorQuery, setTutorQuery] = useState("");
  const [quizId, setQuizId] = useState("mcq_stemi_01");
  const [studentProfile, setStudentProfile] = useState<StudentMasteryProfile>(INITIAL_STUDENT_PROFILE);

  const startDemoJourney = () => {
    setIsDemoActive(true);
    setDemoStepIdx(0);
    setCurrentMode(DEMO_STEPS[0].targetMode);
  };

  const handleSelectDemoStep = (index: number) => {
    if (index >= 0 && index < DEMO_STEPS.length) {
      setDemoStepIdx(index);
      setCurrentMode(DEMO_STEPS[index].targetMode);
    }
  };

  const handleNavigateToTutor = (query: string) => {
    setTutorQuery(query);
    setCurrentMode("tutor");
  };

  const handleNavigateToQuiz = (targetQuizId?: string) => {
    if (targetQuizId) setQuizId(targetQuizId);
    setCurrentMode("quiz");
  };

  const handleNavigateToSim = () => {
    setCurrentMode("simulation");
  };

  const handleAttemptCompleted = (topic: string, isCorrect: boolean) => {
    // Dynamically update candidate profile in memory
    setStudentProfile((prev) => {
      const newAttempts = prev.totalAttempts + 1;
      const newAcc = isCorrect
        ? (prev.overallAccuracy * prev.totalAttempts + 1) / newAttempts
        : (prev.overallAccuracy * prev.totalAttempts) / newAttempts;

      return {
        ...prev,
        totalAttempts: newAttempts,
        overallAccuracy: Number(newAcc.toFixed(2)),
        masteryLevel: newAcc >= 0.8 ? "MASTERY" : newAcc >= 0.7 ? "COMPETENT" : "DEVELOPING",
        weakTopics: isCorrect
          ? prev.weakTopics.filter((t) => !topic.toLowerCase().includes(t.toLowerCase()))
          : prev.weakTopics,
      };
    });
  };

  const showEvidenceHUD = EVIDENCE_HUD_MODES.includes(currentMode);

  return (
    <div className="min-h-screen flex flex-col relative" style={{ background: '#0b1120' }}>

      {/* Top Header Navigation */}
      <CyberHUDNav
        currentMode={currentMode}
        onSelectMode={setCurrentMode}
        userRole={userRole}
        onSwitchRole={(role) => {
          setUserRole(role);
          if (role === "INSTITUTION_ADMIN") {
            setCurrentMode("admin");
          } else if (role === "STUDENT") {
            setCurrentMode("command_center");
          }
        }}
        onOpenPipelineModal={() => setIsPipelineModalOpen(true)}
        onStartDemoJourney={startDemoJourney}
      />

      {/* Contextual Evidence Status Bar — only shown in AI-active modes */}
      {showEvidenceHUD && (
        <AIIntelligenceHUD
          evidenceConfidence={98.6}
          sourceCorpus="NICE NG185, NG128 & BNF 85"
          safetyStatus="VERIFIED"
          personalizationLevel={`${studentProfile.masteryLevel} (${(studentProfile.overallAccuracy * 100).toFixed(0)}%)`}
        />
      )}

      {/* Main Content */}
      <main className="flex-1 pb-16">
        {currentMode === "landing" && (
          <HeroExperience
            onLaunchMode={setCurrentMode}
            onStartDemoJourney={startDemoJourney}
            onOpenPipelineModal={() => setIsPipelineModalOpen(true)}
          />
        )}

        {currentMode === "anatomy" && (
          <IntelligentAnatomyLab
            onNavigateToTutor={handleNavigateToTutor}
            onNavigateToQuiz={handleNavigateToQuiz}
            onNavigateToSim={handleNavigateToSim}
          />
        )}

        {currentMode === "tutor" && (
          <AITutorStudio
            initialPrompt={tutorQuery}
            onNavigateToQuiz={() => handleNavigateToQuiz()}
          />
        )}

        {currentMode === "quiz" && (
          <ClinicalMCQEngine
            initialQuestionId={quizId}
            onNavigateToTutor={handleNavigateToTutor}
            onAttemptCompleted={handleAttemptCompleted}
          />
        )}

        {currentMode === "simulation" && <CaseSimulationRoom />}

        {currentMode === "command_center" && (
          <StudentCommandCenter
            profile={studentProfile}
            onNavigate={setCurrentMode}
          />
        )}

        {currentMode === "admin" && <InstitutionAdminView />}

        {currentMode === "investor" && <InvestorPitchView />}
      </main>

      {/* Guided Demo Stepper HUD */}
      {isDemoActive && (
        <DemoJourneyController
          currentStepIndex={demoStepIdx}
          onSelectStep={handleSelectDemoStep}
          onClose={() => setIsDemoActive(false)}
        />
      )}

      {/* Architecture Pipeline Deep Dive Modal */}
      <HackathonDeepDiveModal
        isOpen={isPipelineModalOpen}
        onClose={() => setIsPipelineModalOpen(false)}
      />
    </div>
  );
}
