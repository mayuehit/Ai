"""
Figures for "Build a Multimodal Model from Scratch"
All figures are generated with matplotlib — no external image files needed.
Call each function inside a Jupyter notebook cell to see the figure inline.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe


# ── Shared style ────────────────────────────────────────────────────────────

BLUE   = "#4A90D9"
GREEN  = "#5CB85C"
ORANGE = "#F0AD4E"
RED    = "#D9534F"
PURPLE = "#9B59B6"
GREY   = "#BDC3C7"
DARK   = "#2C3E50"
WHITE  = "#FFFFFF"

def _box(ax, x, y, w, h, color, text, fontsize=10, text_color=WHITE, radius=0.3):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle=f"round,pad=0.05,rounding_size={radius}",
                         facecolor=color, edgecolor=DARK, linewidth=1.2, zorder=3)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            color=text_color, fontweight='bold', zorder=4)

def _arrow(ax, x1, y1, x2, y2, color=DARK, lw=1.5):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color,
                                lw=lw, mutation_scale=15),
                zorder=2)


# ── Figure 1: Book overview (Chapter 0) ─────────────────────────────────────

def draw_book_overview(save_path=None):
    """High-level pipeline: Image + Text → Multimodal Model → Output."""
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 4)
    ax.axis('off')
    fig.patch.set_facecolor('#F8F9FA')

    # Image input
    img_data = np.ones((8, 8, 3))
    img_data[2:6, 2:6] = [0.3, 0.6, 1.0]   # blue square = "image"
    img_ax = ax.inset_axes([0.01, 0.2, 0.12, 0.6])
    img_ax.imshow(img_data)
    img_ax.set_xticks([]); img_ax.set_yticks([])
    img_ax.set_title("Image", fontsize=9, pad=3)

    _arrow(ax, 1.9, 2.0, 2.7, 2.0)

    # ViT box
    _box(ax, 3.3, 2.0, 1.1, 1.1, BLUE, "ViT\nEncoder", fontsize=9)
    _arrow(ax, 3.9, 2.0, 4.7, 2.0)

    # Projection box
    _box(ax, 5.3, 2.0, 1.1, 0.8, ORANGE, "Projection\nMLP", fontsize=9)
    _arrow(ax, 5.9, 2.0, 6.7, 2.0)

    # Merge arrow from text side
    ax.text(7.0, 3.2, "User: What color is\nthe shape?",
            ha='center', va='center', fontsize=8,
            bbox=dict(boxstyle='round', facecolor='#EBF5FB', edgecolor=BLUE, lw=1))
    _arrow(ax, 7.0, 2.75, 7.0, 2.4)

    # GPT decoder box
    _box(ax, 7.0, 2.0, 1.4, 0.9, GREEN, "GPT\nDecoder", fontsize=9)
    _arrow(ax, 7.7, 2.0, 8.5, 2.0)

    # Output
    ax.text(10.0, 2.0, "\"The shape is blue.\"",
            ha='center', va='center', fontsize=9, style='italic',
            bbox=dict(boxstyle='round', facecolor='#EAFAF1', edgecolor=GREEN, lw=1.2))

    # Chapter labels
    labels = [("Ch 1", 3.3, 0.6), ("Ch 2\n(CLIP)", 5.3, 0.6), ("Ch 3–4", 7.0, 0.6)]
    for txt, x, y in labels:
        ax.text(x, y, txt, ha='center', va='center', fontsize=8,
                color=DARK, style='italic')

    ax.set_title("Build a Multimodal Model from Scratch — Pipeline Overview",
                 fontsize=13, pad=10, fontweight='bold', color=DARK)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches='tight')
    return fig


# ── Figure 2: Patch splitting (Chapter 1) ───────────────────────────────────

def draw_patch_splitting(save_path=None):
    """Show a colorful image being divided into patches."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    fig.patch.set_facecolor('#F8F9FA')

    # Create a simple synthetic image with visible structure
    img_size = 48
    patch_size = 16
    img = np.zeros((img_size, img_size, 3))
    # top-left quadrant: red
    img[:24, :24] = [0.9, 0.3, 0.3]
    # top-right: green
    img[:24, 24:] = [0.3, 0.8, 0.3]
    # bottom-left: blue
    img[24:, :24] = [0.3, 0.4, 0.9]
    # bottom-right: yellow
    img[24:, 24:] = [0.95, 0.85, 0.2]
    # add some texture
    np.random.seed(42)
    img += np.random.rand(img_size, img_size, 3) * 0.12
    img = np.clip(img, 0, 1)

    # Panel 1: original image
    axes[0].imshow(img)
    axes[0].set_title('① Original Image\n(48×48 pixels)', fontsize=11, fontweight='bold')
    axes[0].set_xticks([]); axes[0].set_yticks([])
    for spine in axes[0].spines.values():
        spine.set_edgecolor(BLUE); spine.set_linewidth(2)

    # Panel 2: image with grid overlay
    axes[1].imshow(img)
    n = img_size // patch_size
    for i in range(0, img_size + 1, patch_size):
        axes[1].axhline(i - 0.5, color='white', linewidth=2)
        axes[1].axvline(i - 0.5, color='white', linewidth=2)
    # number the patches
    for row in range(n):
        for col in range(n):
            px = col * patch_size + patch_size // 2
            py = row * patch_size + patch_size // 2
            axes[1].text(px, py, f"P{row*n+col+1}", ha='center', va='center',
                         fontsize=10, color='white', fontweight='bold',
                         path_effects=[pe.withStroke(linewidth=2, foreground='black')])
    axes[1].set_title(f'② Split into {n*n} Patches\n(each {patch_size}×{patch_size} pixels)',
                      fontsize=11, fontweight='bold')
    axes[1].set_xticks([]); axes[1].set_yticks([])

    # Panel 3: patches as a horizontal token sequence
    axes[2].set_xlim(0, n * n + 1)
    axes[2].set_ylim(-0.5, 1.8)
    axes[2].axis('off')
    axes[2].set_title(f'③ Flatten to Token Sequence\n({n*n} vectors of size {patch_size}×{patch_size}×3)',
                      fontsize=11, fontweight='bold')

    colors = [[0.9,0.3,0.3],[0.3,0.8,0.3],[0.3,0.4,0.9],[0.95,0.85,0.2]]
    quadrant = [(0,0),(0,1),(1,0),(1,1)]  # which quadrant each patch is in
    for i in range(n * n):
        row = i // n
        col = i % n
        patch_img = img[row*patch_size:(row+1)*patch_size,
                        col*patch_size:(col+1)*patch_size]
        inset = axes[2].inset_axes([i/(n*n) + 0.01, 0.35, 0.85/(n*n), 0.55])
        inset.imshow(patch_img)
        inset.set_xticks([]); inset.set_yticks([])
        for spine in inset.spines.values():
            spine.set_edgecolor(DARK); spine.set_linewidth(1.5)
        axes[2].text(i/(n*n) + 0.5/(n*n) + 0.01, 0.22, f"t_{i+1}",
                     ha='center', fontsize=9, color=DARK, transform=axes[2].transAxes)

    axes[2].annotate("", xy=(0.97, 0.58), xytext=(0.03, 0.58),
                     xycoords='axes fraction', textcoords='axes fraction',
                     arrowprops=dict(arrowstyle="-", color=GREY, lw=1.5,
                                     linestyle='dashed'))
    plt.suptitle("Key Idea: Treat Image Patches Like Words",
                 fontsize=13, fontweight='bold', color=DARK, y=1.02)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches='tight')
    return fig


# ── Figure 3: Attention mask comparison (Chapter 1) ─────────────────────────

def draw_attention_masks(save_path=None):
    """Side-by-side bidirectional vs causal attention masks."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.patch.set_facecolor('#F8F9FA')
    T = 6
    labels = [f"P{i+1}" for i in range(T)]

    for ax, title, is_causal, color, subtitle in [
        (axes[0], "ViT  —  Bidirectional Attention", False, "Blues",
         "Every patch attends to every other patch"),
        (axes[1], "GPT  —  Causal Attention", True, "Oranges",
         "Each token only attends to past tokens"),
    ]:
        mask = np.ones((T, T))
        if is_causal:
            mask = np.tril(mask)

        im = ax.imshow(mask, cmap=color, vmin=0, vmax=1.3,
                       aspect='equal', interpolation='nearest')

        ax.set_xticks(range(T)); ax.set_yticks(range(T))
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel("Key (attends TO)", fontsize=10)
        ax.set_ylabel("Query (attending FROM)", fontsize=10)
        ax.set_title(f"{title}\n{subtitle}", fontsize=11,
                     fontweight='bold', pad=8)

        # Annotate cells
        for i in range(T):
            for j in range(T):
                val = mask[i, j]
                txt = "✓" if val > 0 else "✗"
                color_txt = DARK if val > 0 else RED
                ax.text(j, i, txt, ha='center', va='center',
                        fontsize=13, color=color_txt, fontweight='bold')

        # Highlight diagonal
        for i in range(T):
            rect = plt.Rectangle((i-0.5, i-0.5), 1, 1,
                                  fill=False, edgecolor=RED, lw=2.5)
            ax.add_patch(rect)

    axes[1].text(3.5, -1.2, "← Blocked (future tokens)",
                 ha='center', fontsize=9, color=RED, style='italic')

    plt.suptitle("Bidirectional vs Causal Attention — The Key Difference",
                 fontsize=13, fontweight='bold', color=DARK)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches='tight')
    return fig


# ── Figure 4: CLIP architecture (Chapter 2) ─────────────────────────────────

def draw_clip_architecture(save_path=None):
    """CLIP dual encoder + contrastive loss diagram."""
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6)
    ax.axis('off')
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#F8F9FA')

    # --- Images column ---
    captions_left = ["🐱 Photo of a cat", "🚗 Photo of a car", "🌲 Forest scene"]
    colors_left = ["#E8F4FD", "#FEF9E7", "#EAFAF1"]
    for i, (cap, col) in enumerate(zip(captions_left, colors_left)):
        y = 5.0 - i * 1.5
        box = FancyBboxPatch((0.2, y - 0.35), 2.0, 0.7,
                             boxstyle="round,pad=0.05",
                             facecolor=col, edgecolor=DARK, linewidth=1)
        ax.add_patch(box)
        ax.text(1.2, y, cap, ha='center', va='center', fontsize=9.5)

    # Image encoder
    _box(ax, 3.5, 3.25, 1.2, 4.2, BLUE, "Vision\nEncoder\n(ViT)", fontsize=10)

    for i in range(3):
        y = 5.0 - i * 1.5
        _arrow(ax, 2.3, y, 2.9, y)

    # Image embeddings
    for i in range(3):
        y = 5.0 - i * 1.5
        _arrow(ax, 4.1, y, 4.7, y)
        _box(ax, 5.1, y, 0.8, 0.5, BLUE, f"I{i+1}", fontsize=9, radius=0.2)

    # --- Texts column ---
    texts_right = ["a photo of a cat", "a photo of a car", "a photo of a forest"]
    for i, txt in enumerate(texts_right):
        y = 5.0 - i * 1.5
        box = FancyBboxPatch((7.5, y - 0.35), 2.5, 0.7,
                             boxstyle="round,pad=0.05",
                             facecolor="#F4ECF7", edgecolor=PURPLE, linewidth=1)
        ax.add_patch(box)
        ax.text(8.75, y, f'"{txt}"', ha='center', va='center', fontsize=8.5,
                style='italic')

    # Text encoder
    _box(ax, 6.5, 3.25, 1.2, 4.2, PURPLE, "Text\nEncoder", fontsize=10)

    for i in range(3):
        y = 5.0 - i * 1.5
        _arrow(ax, 7.5, y, 7.1, y)

    # Text embeddings
    for i in range(3):
        y = 5.0 - i * 1.5
        _arrow(ax, 5.9, y, 5.7, y)
        # already drawn

    # Similarity matrix
    sim_ax = ax.inset_axes([0.72, 0.08, 0.26, 0.84])
    sim = np.array([[0.9, 0.1, 0.1],
                    [0.1, 0.85, 0.15],
                    [0.05, 0.1, 0.92]])
    im = sim_ax.imshow(sim, cmap='RdYlGn', vmin=0, vmax=1, aspect='equal')
    sim_ax.set_xticks([0,1,2]); sim_ax.set_yticks([0,1,2])
    sim_ax.set_xticklabels(["T1","T2","T3"], fontsize=8)
    sim_ax.set_yticklabels(["I1","I2","I3"], fontsize=8)
    sim_ax.set_title("Similarity\nMatrix", fontsize=9, fontweight='bold')
    for i in range(3):
        for j in range(3):
            sim_ax.text(j, i, f"{sim[i,j]:.2f}", ha='center', va='center',
                        fontsize=8, fontweight='bold',
                        color='white' if sim[i,j] > 0.5 else DARK)

    ax.text(11.0, 0.3, "Goal: diagonal HIGH\noff-diagonal LOW",
            ha='center', va='center', fontsize=9, color=DARK,
            bbox=dict(facecolor='white', edgecolor=GREEN, boxstyle='round', lw=1.5))

    ax.set_title("CLIP: Contrastive Language-Image Pre-training",
                 fontsize=13, fontweight='bold', color=DARK, pad=10)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches='tight')
    return fig


# ── Figure 5: InfoNCE intuition (Chapter 2) ─────────────────────────────────

def draw_infonce_intuition(save_path=None):
    """Show what InfoNCE loss maximises/minimises in 2D embedding space."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.patch.set_facecolor('#F8F9FA')

    np.random.seed(7)
    n = 4
    colors_pts = [BLUE, GREEN, ORANGE, RED]
    labels_pts  = ["cat", "car", "dog", "bird"]

    # Before training: random
    img_emb_before = np.random.randn(n, 2) * 0.8
    txt_emb_before = np.random.randn(n, 2) * 0.8

    # After training: matched pairs cluster together
    centers = np.array([[1.5, 1.5], [-1.5, 1.5], [1.5, -1.5], [-1.5, -1.5]])
    img_emb_after = centers + np.random.randn(n, 2) * 0.15
    txt_emb_after = centers + np.random.randn(n, 2) * 0.15

    for ax, img_e, txt_e, title in [
        (axes[0], img_emb_before, txt_emb_before,
         "Before Training\n(random embeddings)"),
        (axes[1], img_emb_after, txt_emb_after,
         "After Training\n(matched pairs aligned)"),
    ]:
        ax.set_xlim(-3, 3); ax.set_ylim(-3, 3)
        ax.axhline(0, color=GREY, lw=0.8); ax.axvline(0, color=GREY, lw=0.8)
        ax.set_facecolor('#FAFAFA')
        ax.set_title(title, fontsize=11, fontweight='bold')

        for i in range(n):
            # draw line connecting matching pair
            ax.plot([img_e[i, 0], txt_e[i, 0]],
                    [img_e[i, 1], txt_e[i, 1]],
                    color=colors_pts[i], lw=1.5, alpha=0.5, linestyle='--')
            ax.scatter(*img_e[i], s=120, color=colors_pts[i],
                       marker='s', zorder=5, edgecolors=DARK, lw=1.2)
            ax.scatter(*txt_e[i], s=120, color=colors_pts[i],
                       marker='o', zorder=5, edgecolors=DARK, lw=1.2)
            ax.text(img_e[i, 0] + 0.12, img_e[i, 1] + 0.12,
                    f"🖼{labels_pts[i]}", fontsize=8)
            ax.text(txt_e[i, 0] + 0.12, txt_e[i, 1] + 0.12,
                    f"📝{labels_pts[i]}", fontsize=8)

    # Legend
    axes[0].scatter([], [], marker='s', color=DARK, label='Image embed')
    axes[0].scatter([], [], marker='o', color=DARK, label='Text embed')
    axes[0].legend(fontsize=9, loc='upper right')
    axes[0].set_xlabel("Embedding dim 1"); axes[0].set_ylabel("Embedding dim 2")
    axes[1].set_xlabel("Embedding dim 1")

    plt.suptitle("InfoNCE Loss: Pull Matching Pairs Together, Push Others Apart",
                 fontsize=12, fontweight='bold', color=DARK)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches='tight')
    return fig


# ── Figure 6: VLM architecture (Chapter 3) ──────────────────────────────────

def draw_vlm_architecture(save_path=None):
    """Complete VLM forward pass with token sequence."""
    fig, ax = plt.subplots(figsize=(15, 5.5))
    ax.set_xlim(0, 15); ax.set_ylim(0, 5.5)
    ax.axis('off')
    fig.patch.set_facecolor('#F8F9FA')

    # Image
    img_data = np.zeros((8, 8, 3))
    img_data[:4, :4] = [0.3, 0.6, 1.0]
    img_data[4:, 4:] = [0.9, 0.5, 0.2]
    img_ax = ax.inset_axes([0.005, 0.3, 0.07, 0.45])
    img_ax.imshow(img_data); img_ax.axis('off')
    img_ax.set_title("Image", fontsize=8)

    _arrow(ax, 1.15, 2.75, 1.65, 2.75)
    _box(ax, 2.15, 2.75, 0.9, 1.4, BLUE, "ViT\nEncoder", fontsize=9)
    ax.text(2.15, 1.75, "196 patch\ntokens", ha='center', fontsize=8,
            color=BLUE, style='italic')
    _arrow(ax, 2.65, 2.75, 3.15, 2.75)

    _box(ax, 3.7, 2.75, 1.0, 1.0, ORANGE, "Proj\nMLP", fontsize=9)
    ax.text(3.7, 4.1, "Vision space\n→ Language space",
            ha='center', fontsize=8, color=ORANGE, style='italic')
    _arrow(ax, 4.25, 2.75, 4.85, 2.75)

    # Token sequence
    visual_tokens = 3   # show 3 representative visual tokens
    text_tokens   = 4   # show 4 text tokens

    token_w = 0.65
    gap = 0.08
    start_x = 5.1

    # Visual tokens
    for i in range(visual_tokens):
        x = start_x + i * (token_w + gap)
        _box(ax, x, 2.75, token_w, 0.6, BLUE,
             f"V{i+1}" if i < visual_tokens - 1 else "...", fontsize=9, radius=0.15)

    # ... dots
    dots_x = start_x + visual_tokens * (token_w + gap)

    # Text tokens
    text_labels = ["USER:", "What", "color", "?"]
    for i, lbl in enumerate(text_labels):
        x = dots_x + i * (token_w + gap)
        _box(ax, x, 2.75, token_w, 0.6, GREEN, lbl, fontsize=8, radius=0.15)

    # Bracket showing sequence concat
    seq_start = start_x - token_w/2 - 0.05
    seq_end   = dots_x + (len(text_labels) - 1) * (token_w + gap) + token_w/2 + 0.05
    ax.annotate("", xy=(seq_end, 2.2), xytext=(seq_start, 2.2),
                arrowprops=dict(arrowstyle="-", color=GREY, lw=1.5))
    ax.text((seq_start + seq_end) / 2, 1.95,
            "[ visual tokens (196) | text tokens ]  →  GPT Decoder",
            ha='center', fontsize=9.5, color=DARK,
            bbox=dict(facecolor='white', edgecolor=GREY, boxstyle='round'))

    # GPT decoder
    _arrow(ax, seq_end + 0.1, 2.75, seq_end + 0.6, 2.75)
    _box(ax, seq_end + 1.15, 2.75, 1.0, 1.2, GREEN, "GPT\nDecoder", fontsize=9)
    _arrow(ax, seq_end + 1.65, 2.75, seq_end + 2.15, 2.75)

    # Output text
    ax.text(seq_end + 2.7, 2.75, '"Blue"',
            ha='center', va='center', fontsize=12, fontweight='bold',
            color=GREEN,
            bbox=dict(facecolor='#EAFAF1', edgecolor=GREEN, boxstyle='round', lw=1.5))

    # Loss masking annotation
    ax.text(6.5, 4.55,
            "⚠ Loss computed on text tokens only (visual tokens masked with −100)",
            ha='center', fontsize=9, color=RED, style='italic',
            bbox=dict(facecolor='#FDEDEC', edgecolor=RED, boxstyle='round', lw=1))

    ax.set_title("VLM Forward Pass: Visual Tokens as a Prefix to the Language Model",
                 fontsize=12, fontweight='bold', color=DARK)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches='tight')
    return fig


# ── Figure 7: Two-stage training (Chapter 4) ────────────────────────────────

def draw_training_stages(save_path=None):
    """Frozen vs trainable components across Stage 1 and Stage 2."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    fig.patch.set_facecolor('#F8F9FA')

    components = ["ViT\nEncoder", "Projection\nMLP", "GPT\nDecoder (LLM)"]
    colors_frozen   = ["#D5D8DC", "#D5D8DC", "#D5D8DC"]
    colors_training = [BLUE, ORANGE, GREEN]

    for ax, stage, frozen_flags, title, subtitle in [
        (axes[0], 1, [True, False, True],
         "Stage 1 — Feature Alignment",
         "Data: image-caption pairs  |  LR: 1e-3  |  Epochs: 1"),
        (axes[1], 2, [True, False, False],
         "Stage 2 — Instruction Tuning",
         "Data: visual Q&A  |  LR: 2e-5  |  Epochs: 3"),
    ]:
        ax.set_xlim(0, 5); ax.set_ylim(0, 5)
        ax.axis('off')
        ax.set_facecolor('#FAFAFA')
        ax.set_title(f"{title}\n{subtitle}", fontsize=10.5,
                     fontweight='bold', pad=6)

        for i, (comp, frozen) in enumerate(zip(components, frozen_flags)):
            y = 3.8 - i * 1.4
            col = colors_frozen[i] if frozen else colors_training[i]
            _box(ax, 2.5, y, 3.0, 0.9, col, comp, fontsize=10)

            status_txt = "❄ FROZEN" if frozen else "🔥 TRAINING"
            status_col = "#7F8C8D" if frozen else RED
            ax.text(4.35, y, status_txt, ha='center', va='center',
                    fontsize=9, color=status_col, fontweight='bold')

        # Arrow between boxes
        for i in range(len(components) - 1):
            y = 3.8 - i * 1.4 - 0.45
            _arrow(ax, 2.5, y, 2.5, y - 0.5)

        # Param count annotation
        trainable = sum(1 for f in frozen_flags if not f)
        ax.text(2.5, 0.35,
                f"Trainable components: {trainable} / {len(components)}",
                ha='center', fontsize=10, color=DARK,
                bbox=dict(facecolor='white', edgecolor=DARK,
                          boxstyle='round', lw=1))

    plt.suptitle("Two-Stage Training Strategy", fontsize=13,
                 fontweight='bold', color=DARK)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches='tight')
    return fig


# ── Convenience: render all figures ─────────────────────────────────────────

def render_all(save_dir="figures"):
    import os
    os.makedirs(save_dir, exist_ok=True)
    fns = [
        ("overview",       draw_book_overview),
        ("patch_split",    draw_patch_splitting),
        ("attn_masks",     draw_attention_masks),
        ("clip_arch",      draw_clip_architecture),
        ("infonce",        draw_infonce_intuition),
        ("vlm_arch",       draw_vlm_architecture),
        ("train_stages",   draw_training_stages),
    ]
    for name, fn in fns:
        path = f"{save_dir}/{name}.png"
        fn(save_path=path)
        print(f"Saved {path}")
    plt.close('all')
