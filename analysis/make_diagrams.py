from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
OUT = Path(__file__).resolve().parent / "report_outputs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family":"serif","font.serif":["Times New Roman","Liberation Serif","DejaVu Serif"],"savefig.dpi":300,"savefig.bbox":"tight"})

def box(ax,x,y,w,h,text,fc="#EFE7F5",ec="#6B3E8E",fs=9.5,bold=False):
    p=FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02,rounding_size=0.08",fc=fc,ec=ec,lw=1.2)
    ax.add_patch(p)
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=fs,fontweight="bold" if bold else "normal",wrap=True)
def arrow(ax,x1,y1,x2,y2):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=12,lw=1.2,color="#333"))

# study flow
fig,ax=plt.subplots(figsize=(9,4.1)); ax.set_xlim(0,12); ax.set_ylim(0,5.6); ax.axis("off")
xs=[0.1,2.5,4.9,7.3,9.7]; w=2.2; h=1.5
labels=["Start screen\nPurpose, data use,\nnickname","6 single videos\n(AI, authentic,\nedited non-AI)","2 video pairs\n+ 1 image pair\n(which is AI?)","Post-quiz\n2 Likert items","Results page\nOwn score, detector\nprediction, leaderboard"]
for x,l in zip(xs,labels): box(ax,x,3.5,w,h,l)
for i in range(4): arrow(ax,xs[i]+w,4.25,xs[i+1],4.25)
ax.text(6.0,5.45,"Participant flow (about 4-6 minutes)",ha="center",fontsize=10.5,fontweight="bold")
box(ax,1.3,1.75,7.6,1.0,"For every media round: answer (AI / not AI / not sure, or left / right / not sure)\nand confidence slider (1 = pure guess, 5 = very confident); response time recorded",fc="#E7F0F7",ec="#3B6EA8",fs=9)
arrow(ax,3.6,3.5,3.6,2.75); arrow(ax,6.0,3.5,6.0,2.75)
box(ax,0.1,0.2,3.3,1.0,"Responses stored\n(Supabase table, local CSV)",fc="#E9F4EC",ec="#2E7D5B")
box(ax,4.3,0.2,3.3,1.0,"Python analysis script\n(cleaning, statistics, figures)",fc="#E9F4EC",ec="#2E7D5B")
box(ax,8.5,0.2,3.3,1.0,"Tables and figures\nfor the report",fc="#E9F4EC",ec="#2E7D5B")
arrow(ax,3.4,0.7,4.3,0.7); arrow(ax,7.6,0.7,8.5,0.7); arrow(ax,3.0,1.75,1.75,1.2)
fig.savefig(OUT / "fig_flow.png"); plt.close(fig)

# org chart
fig,ax=plt.subplots(figsize=(9,4.2)); ax.set_xlim(0,12); ax.set_ylim(0,6); ax.axis("off")
box(ax,3.7,4.9,4.6,0.9,"Delft University of Technology\nExecutive Board and eight faculties",fc="#DDEBF7",ec="#1F4E79",bold=True,fs=10)
fac=["Aerospace\nEngineering","Architecture and\nthe Built\nEnvironment","Civil Engineering\nand Geosciences","Electrical Eng.,\nMathematics and\nComputer Science","Technology,\nPolicy and\nManagement (TPM)","Industrial Design\nEngineering\n(IDE)","Applied\nSciences","Mechanical,\nMaritime and\nMaterials Eng."]
fw=1.36; gap=0.1; x0=0.1
ax.plot([0.1+fw/2,0.1+7*(fw+gap)+fw/2],[4.45,4.45],color="#333",lw=1.2); ax.plot([6,6],[4.9,4.45],color="#333",lw=1.2)
centers=[]
for i,f in enumerate(fac):
    x=x0+i*(fw+gap); hl=i in (4,5)
    box(ax,x,3.1,fw,1.0,f,fc="#EFE7F5" if hl else "#F2F2F2",ec="#6B3E8E" if hl else "#888",fs=6.8,bold=hl)
    ax.plot([x+fw/2,x+fw/2],[4.45,4.1],color="#333",lw=1.2); centers.append(x+fw/2)
box(ax,3.0,0.35,6.0,1.5,"AI DeMoS Lab (TU Delft AI Labs programme)\nLab directors: Dr. O. Kudina (TPM) and Dr. N. Cila (IDE)\nPhD candidates and associated faculty",fc="#E9F4EC",ec="#2E7D5B",fs=9)
arrow(ax,centers[4],3.1,5.2,1.85); arrow(ax,centers[5],3.1,6.8,1.85)
fig.savefig(OUT / "fig_org.png"); plt.close(fig)
