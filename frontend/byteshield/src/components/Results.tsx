"use client";
import { motion } from 'motion/react';
import {
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Info,
  Building2,
  MapPin,
  Search,
  Globe,
  Calendar,
  Building,
  Mail,
  MailWarning,
  MailCheck
} from 'lucide-react';
import { cn } from '../lib/utils';

interface Finding {
  type: string;
  severity: string;
  message: string;
}

interface DomainInfo {
  domain?: string;
  registered?: boolean;
  registrar?: string;
  creation_date?: string;
  expiration_date?: string;
  age_days?: number;
  registrar_country?: string;
}

interface DomainReason {
  type: string;
  severity: string;
  message: string;
}

interface ResultsData {
  id: string;
  company_name: string;
  score: number;
  label: string;
  findings: Finding[];
  evidence: string[];
  actions: string[];
  confidence?: number;
  domain?: string;
  domain_info?: DomainInfo;
  domain_reasons?: DomainReason[];
}

export default function Results({ data }: { data: ResultsData }) {

  const getRiskLevel = (score: number) => {
    if (score >= 80) return 'Danger';
    if (score >= 50) return 'Caution';
    return 'Safe';
  };

  const riskLevel = getRiskLevel(data.score);
  const confidence = data.confidence || 98.4;

  const isSafe = riskLevel === 'Safe';
  const isCaution = riskLevel === 'Caution';
  const isDanger = riskLevel === 'Danger';

  const getFindingIcon = (type: string) => {
    switch (type) {
      case 'agent_verified_company':
        return Building2;
      case 'no_official_listing':
        return Search;
      case 'company_location_missing':
        return MapPin;
      case 'domain_very_new':
      case 'domain_new':
      case 'domain_not_registered':
        return Calendar;
      case 'domain_established':
        return Globe;
      default:
        return Info;
    }
  };

  // Check if domain analysis is available
  const hasDomainInfo = data.domain_info && data.domain;
  const domainAge = data.domain_info?.age_days;

  // Check for MX-related findings
  const mxFinding = data.findings.find(f => f.type === 'no_mx' || f.type === 'null_mx' || f.type === 'mx_records_found');
  const hasMxIssue = mxFinding && (mxFinding.type === 'no_mx' || mxFinding.type === 'null_mx');
  const hasMxValid = mxFinding && mxFinding.type === 'mx_records_found';

  return (
    <motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  className="w-full max-w-6xl mx-auto space-y-12 pb-32 px-4"
>
  {/* Two Column Cards */}
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

    {/* Risk Score Card */}
    <div className="glass rounded-[2rem] p-10 flex flex-col items-center justify-start border-white/10">

      {/* Title Wrapper (FIXED ALIGNMENT) */}
      <div className="h-[40px] flex items-center justify-center mb-6">
        <h3 className="text-lg uppercase tracking-[0.45em] text-foreground/60 leading-none">
          Risk Score
        </h3>
      </div>

      {/* Score Circle */}
      <div className="relative w-48 h-48 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="96"
            cy="96"
            r="86"
            stroke="currentColor"
            strokeWidth="7"
            fill="transparent"
            className="text-foreground/10"
          />
          <motion.circle
            cx="96"
            cy="96"
            r="86"
            stroke="currentColor"
            strokeWidth="7"
            fill="transparent"
            strokeDasharray="540"
            initial={{ strokeDashoffset: 540 }}
            animate={{ strokeDashoffset: 540 - (540 * data.score) / 100 }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            className={cn(
              isDanger
                ? "text-danger"
                : isCaution
                ? "text-caution"
                : "text-safe"
            )}
            strokeLinecap="round"
          />
        </svg>

        {/* Score Number */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className={cn(
              "text-7xl md:text-8xl font-bold font-display tracking-tight",
              "dark:drop-shadow-[0_0_20px_rgba(255,255,255,0.15)]",
              isDanger
                ? "text-danger dark:drop-shadow-[0_0_20px_rgba(255,0,0,0.4)]"
                : isCaution
                ? "text-caution dark:drop-shadow-[0_0_20px_rgba(255,200,0,0.4)]"
                : "text-safe dark:drop-shadow-[0_0_20px_rgba(0,255,150,0.4)]"
            )}
          >
            {data.score}
          </span>

          <span className="text-xs text-foreground/40 uppercase tracking-[0.3em] mt-1">
            Score
          </span>
        </div>
      </div>
    </div>


    {/* Risk Level Card */}
    <div className="glass rounded-[2rem] p-10 flex flex-col items-center justify-start border-white/10">

      {/* Title Wrapper (SAME HEIGHT = PERFECT ALIGNMENT) */}
      <div className="h-[40px] flex items-center justify-center mb-6">
        <h3 className="text-lg uppercase tracking-[0.45em] text-foreground/60 leading-none">
          Risk Level
        </h3>
      </div>

      {/* Icon */}
      <div
        className={cn(
          "w-32 h-32 rounded-full flex items-center justify-center mb-8 border",
          isDanger
            ? "bg-danger/10 border-danger/30"
            : isCaution
            ? "bg-caution/10 border-caution/30"
            : "bg-safe/10 border-safe/30"
        )}
      >
        {isDanger && <ShieldX className="w-14 h-14 text-danger" />}
        {isCaution && <ShieldAlert className="w-14 h-14 text-caution" />}
        {isSafe && <ShieldCheck className="w-14 h-14 text-safe" />}
      </div>

      {/* Risk Text */}
      <div
        className={cn(
          "text-3xl md:text-4xl font-semibold tracking-tight",
          isDanger
            ? "text-danger"
            : isCaution
            ? "text-caution"
            : "text-safe"
        )}
      >
        {riskLevel}
      </div>


    </div>

  </div>

  {/* ================= DOMAIN DETAILS (if available) ================= */}
  {hasDomainInfo && (
    <div className="glass rounded-[2rem] p-10 space-y-6 border-white/10">
      <h3 className="text-2xl font-light tracking-tight flex items-center gap-3">
        <Globe className="w-6 h-6" />
        Domain Analysis
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Domain */}
        <div className="p-4 rounded-xl bg-foreground/[0.03] dark:bg-white/[0.03]">
          <p className="text-xs text-foreground/40 uppercase tracking-wider mb-1">Domain</p>
          <p className="font-medium">{data.domain}</p>
        </div>

        {/* Age */}
        <div className="p-4 rounded-xl bg-foreground/[0.03] dark:bg-white/[0.03]">
          <p className="text-xs text-foreground/40 uppercase tracking-wider mb-1">Age</p>
          <p className="font-medium">
            {domainAge !== null && domainAge !== undefined ? (
              domainAge < 30 ? (
                <span className="text-danger">{domainAge} days (New)</span>
              ) : domainAge < 90 ? (
                <span className="text-caution">{domainAge} days</span>
              ) : (
                <span className="text-safe">{domainAge} days</span>
              )
            ) : (
              <span className="text-foreground/60">Unknown</span>
            )}
          </p>
        </div>

        {/* Registrar */}
        <div className="p-4 rounded-xl bg-foreground/[0.03] dark:bg-white/[0.03]">
          <p className="text-xs text-foreground/40 uppercase tracking-wider mb-1">Registrar</p>
          <p className="font-medium">{data.domain_info?.registrar || 'Unknown'}</p>
        </div>

        {/* Registered Status */}
        <div className="p-4 rounded-xl bg-foreground/[0.03] dark:bg-white/[0.03]">
          <p className="text-xs text-foreground/40 uppercase tracking-wider mb-1">Status</p>
          <p className="font-medium">
            {data.domain_info?.registered ? (
              <span className="text-safe">Registered</span>
            ) : (
              <span className="text-danger">Not Registered</span>
            )}
          </p>
        </div>
      </div>

      {/* Domain Risk Reasons */}
      {data.domain_reasons && data.domain_reasons.length > 0 && (
        <div className="space-y-3 mt-4">
          <p className="text-sm text-foreground/60">Domain Risk Factors:</p>
          {data.domain_reasons.map((reason, idx) => {
            const IconComponent = getFindingIcon(reason.type);
            const isHigh = reason.severity === 'high';
            const isSafe = reason.severity === 'safe';

            return (
              <div key={idx} className="p-3 rounded-lg bg-foreground/[0.03] flex gap-3 items-center">
                <div className={cn(
                  "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
                  isHigh ? "bg-danger/10 text-danger" :
                  isSafe ? "bg-safe/10 text-safe" :
                  "bg-caution/10 text-caution"
                )}>
                  <IconComponent className="w-4 h-4" />
                </div>
                <span className={cn(
                  "text-sm",
                  isHigh ? "text-danger" :
                  isSafe ? "text-safe" :
                  "text-foreground/80"
                )}>
                  {reason.message}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  )}

  {/* ================= EMAIL/MX ANALYSIS ================= */}
  {hasDomainInfo && (
    <div className="glass rounded-[2rem] p-10 space-y-6 border-white/10">
      <h3 className="text-2xl font-light tracking-tight flex items-center gap-3">
        <Mail className="w-6 h-6" />
        Mail Server Check
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Email Status */}
        <div className={cn(
          "p-4 rounded-xl",
          hasMxIssue ? "bg-danger/10 border border-danger/30" :
          hasMxValid ? "bg-safe/10 border border-safe/30" :
          "bg-foreground/[0.03] dark:bg-white/[0.03]"
        )}>
          <p className="text-xs text-foreground/40 uppercase tracking-wider mb-1">Can Receive Mail?</p>
          <div className="flex items-center gap-2">
            {hasMxIssue && <MailWarning className="w-5 h-5 text-danger" />}
            {hasMxValid && <MailCheck className="w-5 h-5 text-safe" />}
            {!hasMxIssue && !hasMxValid && <Mail className="w-5 h-5 text-foreground/60" />}
            <p className={cn(
              "font-medium",
              hasMxIssue ? "text-danger" :
              hasMxValid ? "text-safe" :
              "text-foreground/60"
            )}>
              {hasMxIssue ? "No - Cannot Receive Mail" :
               hasMxValid ? "Yes - Can Receive Mail" :
               "Unknown"}
            </p>
          </div>
        </div>

        {/* Domain Info */}
        <div className="p-4 rounded-xl bg-foreground/[0.03] dark:bg-white/[0.03]">
          <p className="text-xs text-foreground/40 uppercase tracking-wider mb-1">Domain</p>
          <p className="font-medium">{data.domain}</p>
        </div>
      </div>

      {/* MX Warning/Success Message */}
      {mxFinding && (
        <div className={cn(
          "p-4 rounded-xl flex gap-3 items-center",
          hasMxIssue ? "bg-danger/10 text-danger" :
          hasMxValid ? "bg-safe/10 text-safe" :
          "bg-foreground/[0.03]"
        )}>
          {hasMxIssue && <MailWarning className="w-5 h-5 flex-shrink-0" />}
          {hasMxValid && <MailCheck className="w-5 h-5 flex-shrink-0" />}
          <span className="text-sm">{mxFinding.message}</span>
        </div>
      )}
    </div>
  )}

      {/* ================= FINDINGS ================= */}
      <div className="glass rounded-[2rem] p-10 space-y-6 border-white/10">

        <h3 className="text-2xl font-light tracking-tight">
          Findings
        </h3>

        <div className="space-y-4">
          {data.findings.map((finding, idx) => {
            const IconComponent = getFindingIcon(finding.type);
            const isHigh = finding.severity !== 'low' && finding.severity !== 'safe';

            return (
              <div key={idx}
                className="p-4 rounded-xl bg-foreground/[0.03] dark:bg-white/[0.03] flex gap-4">

                <div className={cn(
                  "w-10 h-10 rounded-lg flex items-center justify-center",
                  isHigh ? "bg-blue-500/10 text-blue-400" : "bg-green-500/10 text-green-500"
                )}>
                  <IconComponent className="w-5 h-5" />
                </div>

                <div>
                  <p className="font-medium capitalize">
                    {finding.type.replace(/_/g, ' ')}
                  </p>
                  <p className="text-sm text-foreground/60">
                    {finding.message}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ================= EVIDENCE (FULL WIDTH) ================= */}
      <div className="glass rounded-[2rem] p-10 space-y-6 border-white/10">

        <h3 className="text-2xl font-light tracking-tight">
          Evidence
        </h3>

        <div className="space-y-4">
          {data.evidence.map((item, idx) => (
            <div key={idx}
              className="p-4 rounded-xl bg-foreground/[0.03] dark:bg-white/[0.03]">
              <p className="text-foreground/80">{item}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ================= ACTIONS BELOW ================= */}
      <div className="glass rounded-[2rem] p-10 space-y-6 border-white/10">

        <h3 className="text-2xl font-light tracking-tight">
          Recommended Steps
        </h3>

        <div className="space-y-4">
          {data.actions.map((action, idx) => (
            <div key={idx}
              className="flex gap-4 items-start p-4 rounded-xl bg-foreground/[0.03] dark:bg-white/[0.03]">

              <div className="w-8 h-8 flex items-center justify-center rounded-full bg-foreground/10 dark:bg-white/10 text-sm font-medium">
                {idx + 1}
              </div>

              <p className="text-foreground/80">
                {action}
              </p>
            </div>
          ))}
        </div>
      </div>

    </motion.div>
  );
}