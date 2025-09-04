# Customer Management Unit

## Unit Overview
The Customer Management Unit handles customer registration, onboarding, and profile management. This unit is responsible for the initial customer journey and maintaining customer account information.

## Business Capability
- Customer registration and account creation
- Program onboarding and education
- Customer profile management
- Initial tier assignment (Bronze)

## User Stories

### US001: Customer Registration
**As a** new customer  
**I want** to register for the loyalty and rewards program  
**So that** I can start earning points on my card purchases

**Acceptance Criteria:**
- Given I am a new customer, when I provide my card details and personal information, then my account should be created with Bronze tier status
- Given I complete registration, when I make my first purchase, then I should start earning base points immediately
- Given I register successfully, when I log into the system, then I should see my current tier status and available benefits

### US002: Program Onboarding Tutorial
**As a** newly registered customer  
**I want** to understand how the rewards program works  
**So that** I can maximize my point earning potential

**Acceptance Criteria:**
- Given I am a new member, when I first access the program, then I should see an interactive tutorial explaining tier benefits
- Given I complete the tutorial, when I view my dashboard, then I should see personalized recommendations for earning more points
- Given I finish onboarding, when I make purchases, then I should receive notifications about points earned

## Data Ownership
- Customer profiles and personal information
- Registration status and onboarding progress
- Customer preferences and settings
- Initial tier assignment

## External Dependencies
- Card validation services
- Identity verification services
- Email/SMS notification services

## Events Published
- CustomerRegistered
- CustomerOnboardingCompleted
- CustomerProfileUpdated

## Events Consumed
- None (entry point to the system)

## Team Size
Recommended: 2-3 developers (Frontend + Backend + QA)