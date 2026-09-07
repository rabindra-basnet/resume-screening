describe("TalentPulse AI - E2E Application Flows", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("should render the landing page with navigation links and CTA button", () => {
    cy.contains("TalentPulse AI").should("be.visible");
    cy.contains("Resume Screening AI").should("be.visible");
    cy.contains("Agentic Workspace").should("be.visible");
  });

  it("should navigate to the single-screen Agentic Workspace at /screen", () => {
    cy.contains("Agentic Workspace").click();
    cy.url().should("include", "/screen");
    cy.contains("Get your resume ready in three steps").should("be.visible");

    // Verify inline workspace tabs
    cy.contains("Screen Resume").should("be.visible");
    cy.contains("Job Descriptions").should("be.visible");
    cy.contains("Learning Roadmap").should("be.visible");
  });

  it("should switch inline workspace tabs on the same screen without route reload", () => {
    cy.visit("/screen");

    // Click Job Descriptions tab
    cy.contains("Job Descriptions").click();
    cy.contains("Create, parse, and reference job requirements").should("be.visible");

    // Click Learning Roadmap tab
    cy.contains("Learning Roadmap").click();
    cy.contains("Targeted courses, tutorials, and materials").should("be.visible");

    // Return to Screen Resume tab
    cy.contains("Screen Resume").click();
    cy.contains("Upload & Review").should("be.visible");
  });

  it("should navigate to the Login page when clicking Sign In", () => {
    cy.contains("Sign In").click();
    cy.url().should("include", "/login");
    cy.contains("Sign in to your account").should("be.visible");
    cy.contains("Continue with Google").should("be.visible");
  });
});
