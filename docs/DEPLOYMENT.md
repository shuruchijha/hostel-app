# HostelHub: Setup & Deployment Guide

## 1. Prerequisites Checklist

To build and run HostelHub locally, you will need:
1. **Node.js (v20+ LTS)** and **npm**
2. **Git**
3. A free **Supabase** account ([https://supabase.com](https://supabase.com))
4. (Optional for production) A free **Vercel** account ([https://vercel.com](https://vercel.com))

---

## 2. Local Environment Setup

### Step 2.1: Installing Node.js LTS (Windows)
If Node.js is not yet installed on your system, you can install it via PowerShell or directly from the official website:
```powershell
# Option A: Via Windows Package Manager (winget)
winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements

# Option B: Direct Installer
# Download and run the 64-bit LTS installer from https://nodejs.org
```
*Note: Restart your terminal window after installing so `node` and `npm` are added to your system PATH.*

### Step 2.2: Clone & Install Dependencies
```bash
git status
npm install
```

### Step 2.3: Configure Environment Variables
1. Copy the provided `.env.example` file to create `.env.local`:
   ```bash
   cp .env.example .env.local
   ```
2. Open `.env.local` and fill in your Supabase project credentials (see Step 3 below).

---

## 3. Supabase Project Setup (Manual Steps for User)

> **Important**: Antigravity cannot create external accounts on your behalf. Follow these exact steps to connect your database:

1. Go to [https://supabase.com](https://supabase.com) and click **Start your project** (log in with GitHub or email).
2. Click **New Project**:
   - **Name**: `hostelhub-prod` (or `hostelhub-dev`)
   - **Database Password**: Choose a strong password and save it safely.
   - **Region**: Choose the region closest to your campus/users (e.g. `South Asia (Mumbai)` or `US East`).
   - Click **Create new project**.
3. Retrieve your API Keys:
   - Navigate to **Project Settings** -> **API**.
   - Copy **Project URL** -> Paste into `NEXT_PUBLIC_SUPABASE_URL` in `.env.local`.
   - Copy **Project API Keys (`anon` `public`)** -> Paste into `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `.env.local`.
   - Copy **Project API Keys (`service_role` `secret`)** -> Paste into `SUPABASE_SERVICE_ROLE_KEY` in `.env.local`.
4. Apply Database Migrations:
   - Navigate to the **SQL Editor** tab in the Supabase Dashboard.
   - Paste the SQL script from `supabase/migrations/001_initial_schema.sql` (generated in Phase 2).
   - Click **Run** to provision tables, triggers, and RLS policies.

---

## 4. Running the Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 5. Production Deployment to Vercel

1. Push your repository to GitHub.
2. Sign in to [Vercel](https://vercel.com) and click **Add New** -> **Project**.
3. Import your `Hostel App` repository.
4. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `NEXT_PUBLIC_APP_URL` (set to your Vercel deployment URL, e.g. `https://hostelhub.vercel.app`)
5. Click **Deploy**. Vercel will automatically build and publish your Next.js application.
