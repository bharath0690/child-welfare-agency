# Binti AI journeys (concept prototype)

A static, no-build prototype of three journeys: **Caseworker**, **Prospective foster or adoptive parent** and **Kin caregiver**. All names and data are fictional. AI responses are scripted. It is not an official Binti product.

The persona canvas that these journeys come from is in `canvas/index.html` (served at `/canvas` on Vercel).

## Run it locally
```bash
npm run dev        # or: python3 -m http.server 3000
```
Open http://localhost:3000. Routes look like `#/caseworker/3`, `#/parent/2`, `#/kin/0`.

## Put it on GitHub
```bash
cd binti-prototype
git init -b main
git add .
git commit -m "Initial prototype"
# create an empty repo on github.com first (no README), then:
git remote add origin https://github.com/<you>/binti-prototype.git
git push -u origin main
```

## Deploy on Vercel (public link, no sign-in for viewers)
1. Go to vercel.com/new and import the GitHub repo.
2. Framework preset: **Other**. Leave build command and output directory empty. Deploy.
3. Every push to `main` redeploys. Share the `*.vercel.app` URL.

If the link asks viewers to log in to Vercel, turn off **Deployment Protection** (Project, Settings, Deployment Protection) for production.

CLI alternative: `npx vercel --prod`.

## Files
| File | What it holds |
|---|---|
| `data.js` | The three journeys (stages, today and product feeling, modules) from the persona canvas |
| `app.js` | State, hash routing, shell, chat, rating and the AI quality drawer |
| `screens-caseworker.js` | Seven caseworker screens |
| `screens-family.js` | Seven screens each for the parent and kin caregiver |
| `styles.css` | Light and dark themes |

## Adding the real AI features
Each AI moment is a scripted string in a screens file, wrapped with `H.aiBanner` and `H.rate`. To go live later, replace the scripted text with a call to a Vercel serverless function in `/api` that holds the model API key on the server. Keep fictional data only until privacy review.
