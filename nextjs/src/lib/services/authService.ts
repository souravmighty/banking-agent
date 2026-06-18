import { 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut, 
  sendEmailVerification,
  User,
  getIdToken
} from "firebase/auth";
import { auth } from "@/firebase/config";
import { customerIdentityService, CustomerMeResponse } from "./customerIdentityService";

export class AuthService {
  /**
   * Helper to get the current Firebase user.
   */
  getCurrentFirebaseUser(): User | null {
    return auth.currentUser;
  }

  /**
   * Helper to get or refresh the current Firebase ID Token.
   */
  async getIdToken(forceRefresh = false): Promise<string | null> {
    const user = auth.currentUser;
    if (!user) return null;
    return await getIdToken(user, forceRefresh);
  }

  /**
   * Complete signup flow for an existing bank customer.
   * 
   * 1. Checks if email is pre-authorized.
   * 2. If valid and not registered, creates Firebase account.
   * 3. Sends email verification.
   * 4. Signs out so they can't access pages until verified.
   */
  async register(email: string, password: string): Promise<void> {
    // 1. Check if they are an existing customer and not yet registered
    const checkRes = await customerIdentityService.checkEmail(email);
    
    if (!checkRes.customer_exists) {
      throw new Error("Not a valid bank customer. Please contact your bank.");
    }
    
    if (checkRes.already_registered) {
      throw new Error("This email is already registered. Please proceed with login.");
    }

    // 2. Create the Firebase account
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;

    // 3. Send verification email with explicit language configuration
    try {
      auth.languageCode = "en";
      await sendEmailVerification(user);
    } catch (emailError) {
      console.error("Failed to send initial verification email:", emailError);
      throw new Error(`Account created, but failed to send verification email: ${(emailError as Error).message || "Firebase Auth email service error."}`);
    }

    // 4. Force sign out immediately after registration to block access until email is verified
    await signOut(auth);
  }

  /**
   * Complete login and session initialization flow.
   * 
   * 1. Check if email is pre-authorized.
   * 2. Perform Firebase sign in.
   * 3. Enforce email verification.
   * 4. Link Firebase UID if this is the first login.
   * 5. Get and return customer profile context.
   */
  async login(email: string, password: string): Promise<CustomerMeResponse> {
    // 1. Check email pre-authorization state
    const checkRes = await customerIdentityService.checkEmail(email);
    
    if (!checkRes.customer_exists) {
      throw new Error("Not a valid bank customer. Please contact your bank.");
    }

    // 2. Sign in with Firebase
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;

    // 3. Check if email is verified
    if (!user.emailVerified) {
      // Automatically resend verification email to assist onboarding
      try {
        auth.languageCode = "en";
        await sendEmailVerification(user);
      } catch (sendError) {
        console.error("Failed to resend verification email on login attempt:", sendError);
      }
      
      // Sign out to prevent unverified session access
      await signOut(auth);
      throw new Error("Verification email sent. Please verify your email before logging in.");
    }

    // 4. Obtain Firebase ID token
    const token = await user.getIdToken();

    // 5. Handle linking if registration is not completed yet
    if (!checkRes.already_registered) {
      try {
        await customerIdentityService.linkUser(token);
      } catch (linkError) {
        console.error("Linking failed:", linkError);
        await signOut(auth);
        throw new Error(`Onboarding linking failed: ${(linkError as Error).message || "Service unavailable"}`);
      }
    }

    // 6. Fetch and return customer profile context (Session Initialization)
    try {
      return await customerIdentityService.getMe(token);
    } catch (meError) {
      console.error("Fetching profile context failed:", meError);
      await signOut(auth);
      throw new Error(`Failed to load customer profile: ${(meError as Error).message || "Service unavailable"}`);
    }
  }

  /**
   * Sign out of Firebase and clean up session state.
   */
  async logout(): Promise<void> {
    await signOut(auth);
  }
}

export const authService = new AuthService();
