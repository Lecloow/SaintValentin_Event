import { StorageService } from './storage';

interface Question {
  id: number;
  text: string;
  options: string[];
}

const questions: Question[] = [
  {
    id: 3,
    text: "Quel est ton style de musique préféré ?",
    options: ["Rap", "Pop", "Rock", "Autre"]
  },
  {
    id: 4,
    text: "Quel est pour toi le voyage idéal ?",
    options: ["Voyage en famille", "Voyage entre amis", "Voyage en couple", "Voyage solo"]
  },
  {
    id: 5,
    text: "Quelle est ta destination de rêve ?",
    options: ["Londres", "Séoul", "Marrakech", "Rio de Janeiro"]
  },
  {
    id: 6,
    text: "Quel est ton genre de film/série préféré ?",
    options: ["Science-Fiction", "Drame", "Comédie", "Action"]
  },
  {
    id: 7,
    text: "Tu passes le plus de temps sur :",
    options: ["Instagram", "Snapchat", "TikTok", "Je ne suis pas vraiment sur les réseaux"]
  },
  {
    id: 8,
    text: "A l'école tu préfères :",
    options: ["Histoire-Géographie", "Anglais", "Sport", "Français/Philosophie"]
  },
  {
    id: 9,
    text: "Au petit-déjeuner c'est plutôt :",
    options: ["Café/Thé", "Jus de fruit", "Eau", "Soda"]
  },
  {
    id: 10,
    text: "A Passy, le midi tu préfères être :",
    options: ["Dehors", "Dans l'atrium", "Dans la cour", "En salle Verte/Bleue"]
  },
  {
    id: 11,
    text: "Avec 1.000.000 d'euros tu ferais plutôt :",
    options: ["Un don à un association", "L'achat d'une maison dans le Sud", "Un investissement boursier", "Du shopping sur les Champs"]
  },
  {
    id: 12,
    text: "Comme super pouvoir, tu préfèrerais pouvoir :",
    options: ["Voler", "Etre invisible", "Lire dans les pensée", "Remonter le temps"]
  },
  {
    id: 13,
    text: "Quelle est ta saison préférée :",
    options: ["Été", "Automne", "Hiver", "Printemps"]
  },
  {
    id: 14,
    text: "Tu préfères lire :",
    options: ["Des romans", "Des BD/mangas", "Les journaux", "Lire ?"]
  },
  {
    id: 15,
    text: "Tu préfères pratiquer quel sport :",
    options: ["Sport de raquette", "Sport collectif", "Sport de performance (athlétisme, natation...)", "Sport de combat"]
  },
  {
    id: 16,
    text: "Quelle est ta soirée idéale ?",
    options: ["Soirée cinéma", "Soirée entre amis", "Soirée dodo", "Soirée gaming"]
  },
  {
    id: 17,
    text: "Si tu pouvais dîner avec une personne historique ce serait :",
    options: ["Michael Jackson", "Jules César", "Pelé", "Pythagore (même si t'as oublié son théorème)"]
  }
];

export class QuestionnairePage {
  private contentEl: HTMLElement | null = null;
  private answers: Map<number, number> = new Map();

  constructor() {
    this.init();
  }

  private init(): void {
    this.contentEl = document.getElementById('content');
    const user = StorageService.getUser();

    if (!user) {
      this.renderNotConnected();
      return;
    }

    this.render(user);
  }

  private renderNotConnected(): void {
    if (!this.contentEl) return;

    this.contentEl.innerHTML = `
      <div class="error-message">Vous n'êtes pas connecté. Redirection...</div>
    `;

    setTimeout(() => {
      window.location.href = './index.html';
    }, 2000);
  }

  private render(user: any): void {
    if (!this.contentEl) return;

    const questionsHTML = questions.map(q => this.renderQuestion(q)).join('');

    this.contentEl.innerHTML = `
      <div class="greeting">Bonjour ${user.first_name}! 👋</div>
      <p style="text-align: center; color: #666; margin-bottom: 2rem;">
        Réponds à ces questions pour trouver ton âme sœur pour la Saint-Valentin!
      </p>
      
      <form id="questionnaireForm" class="questionnaire-form">
        ${questionsHTML}
        
        <button type="submit" class="submit-button" id="submitBtn">
          Envoyer mes réponses
        </button>
      </form>
      
      <div id="message"></div>
    `;

    this.attachEventListeners(user.id);
  }

  private renderQuestion(question: Question): string {
    return `
      <div class="question">
        <div class="question-title">
          <span class="question-number">${question.id}.</span>
          ${question.text}
        </div>
        <div class="options">
          ${question.options.map((option, index) => `
            <label class="option">
              <input 
                type="radio" 
                name="q${question.id}" 
                value="${index + 1}" 
                required
              />
              <span class="option-label">${option}</span>
            </label>
          `).join('')}
        </div>
      </div>
    `;
  }

  private attachEventListeners(userId: string): void {
    const form = document.getElementById('questionnaireForm') as HTMLFormElement;
    
    if (form) {
      form.addEventListener('submit', (e) => this.handleSubmit(e, userId));
      
      // Track answer changes
      const inputs = form.querySelectorAll('input[type="radio"]');
      inputs.forEach(input => {
        input.addEventListener('change', (e) => {
          const target = e.target as HTMLInputElement;
          const questionId = parseInt(target.name.substring(1));
          const value = parseInt(target.value);
          this.answers.set(questionId, value);
        });
      });
    }
  }

  private async handleSubmit(event: Event, userId: string): Promise<void> {
    event.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn') as HTMLButtonElement;
    const messageDiv = document.getElementById('message');
    
    if (!submitBtn || !messageDiv) return;

    // Validate all questions are answered
    if (this.answers.size !== questions.length) {
      messageDiv.innerHTML = `
        <div class="error-message">
          Veuillez répondre à toutes les questions (${this.answers.size}/${questions.length} réponses)
        </div>
      `;
      return;
    }

    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.textContent = 'Envoi en cours...';
    messageDiv.innerHTML = '<div class="loading">Envoi de vos réponses...</div>';

    try {
      // Build payload
      const payload: any = { user_id: userId };
      for (let i = 3; i <= 17; i++) {
        payload[`q${i}`] = this.answers.get(i) || 1;
      }

      const API_BASE_URL = 'https://saint-valentin-backend-tyqw.onrender.com';
      const response = await fetch(`${API_BASE_URL}/submit-answers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Erreur ${response.status}`);
      }

      const result = await response.json();
      
      messageDiv.innerHTML = `
        <div class="success-message">
          ✅ ${result.message || 'Réponses enregistrées avec succès!'}
          <br><br>
          Redirection vers votre profil...
        </div>
      `;

      setTimeout(() => {
        window.location.href = './profile.html';
      }, 2000);

    } catch (error) {
      console.error('Error submitting answers:', error);
      messageDiv.innerHTML = `
        <div class="error-message">
          ❌ Erreur lors de l'envoi: ${error instanceof Error ? error.message : 'Erreur inconnue'}
        </div>
      `;
      submitBtn.disabled = false;
      submitBtn.textContent = 'Envoyer mes réponses';
    }
  }
}

// Initialise la page quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
  new QuestionnairePage();
});
