# How to Upload This Lab to GitHub

Follow these steps to publish your Africa SP NOC Lab portfolio on GitHub.

---

## Step 1 — Create the GitHub Repository

1. Go to https://github.com/new
2. Set repository name: `africa-sp-noc-lab`
3. Set visibility: **Public** (required for portfolio)
4. Add description: `Cisco CML lab simulating an African SP NOC with MPLS BGP L3VPN - Portfolio`
5. Leave README unchecked (you have your own)
6. Click **Create repository**

---

## Step 2 — Initialize and Push from Your Computer

```bash
# Navigate to the lab folder
cd africa-sp-noc-lab

# Initialize git
git init
git add .
git commit -m "Initial commit: Africa SP NOC Lab with MPLS BGP topology"

# Connect to your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/africa-sp-noc-lab.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 3 — Add Recommended GitHub Topics

In your repository settings, add these topics for discoverability:

```
cisco  mpls  bgp  cml  networking  noc  service-provider  ccnp  iosv  l3vpn
```

---

## Step 4 — Add to Your LinkedIn Portfolio

1. Go to your LinkedIn profile
2. Click **Add section → Featured → Links**
3. Paste your GitHub repo URL
4. Title: `Africa SP NOC Lab — MPLS/BGP CML Portfolio`
5. Description: `Cisco CML lab simulating a telecom SP NOC with MPLS L3VPN, BGP route reflectors, VRF, and 5 real NOC troubleshooting scenarios.`

---

## Step 5 — Pin the Repository on GitHub

1. Go to your GitHub profile page
2. Click **Customize your pins**
3. Select `africa-sp-noc-lab`
4. This makes it appear prominently on your profile

---

## Optional: Add a Lab Screenshot

Once you have the lab running in CML:
1. Take a screenshot of the running topology in CML Web UI
2. Save as `docs/cml-topology-screenshot.png`
3. Add this line to your README.md under the topology section:

```markdown
![CML Lab Topology](docs/cml-topology-screenshot.png)
```

4. Commit and push the image.

---

## Your Portfolio URL

After pushing:
```
https://github.com/YOUR_USERNAME/africa-sp-noc-lab
```

Include this URL in:
- CV / Resume under "Technical Projects"
- LinkedIn profile "Featured" section  
- Cover letter for NOC / SP network engineer roles
