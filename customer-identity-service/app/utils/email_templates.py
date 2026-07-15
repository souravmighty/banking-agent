def get_approval_email_html(name: str, email: str, expiry_formatted: str) -> str:
    """
    Generates a premium, theme-maintaining HTML email template for demo approval notifications.
    """
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Welcome to BankPilot</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #334155;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f5f7fb; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 640px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.03), 0 4px 6px -4px rgba(0, 0, 0, 0.03); border: 1px solid #E5E7EB;">
          
          <!-- Header Gradient Banner (ABC Bank Theme) -->
          <tr>
            <td align="center" style="background: linear-gradient(135deg, #1a1f71 0%, #312e81 100%); padding: 32px;">
              <h1 style="margin: 0; color: #ffffff; font-size: 30px; font-weight: 800; letter-spacing: -0.5px;">
                BankPilot
              </h1>
              <p style="margin: 6px 0 0 0; color: #E3F2FD; font-size: 15px; opacity: 0.9;">
                Production-Inspired AI Banking Platform
              </p>
            </td>
          </tr>
          
          <!-- Content Body -->
          <tr>
            <td style="padding: 32px; line-height: 1.6; font-size: 15px;">
              
              <p style="font-size: 17px; margin: 0 0 16px 0; color: #1e293b;">
                Hi <strong>{name}</strong>,
              </p>
              
              <p style="margin: 0 0 16px 0;">
                Your request has been approved and your environment is now ready! 
                Your demo access is active and will expire on <strong>{expiry_formatted}</strong>.
              </p>
              
              <p style="margin: 0 0 24px 0; font-size: 14px; color: #64748b; background: #faf5ff; border: 1px solid #f3e8ff; padding: 12px; border-radius: 8px;">
                🔒 <strong>Privacy Note:</strong> A secure, <strong>synthetic customer profile</strong> has been assigned to your session. 
                All account details, transactions, and balances are entirely simulated for demonstration purposes.
              </p>
              
              <h2 style="color: #1a1f71; font-size: 18px; font-weight: 800; letter-spacing: -0.5px; margin: 0 0 12px 0; border-bottom: 2px solid #f1f5f9; padding-bottom: 6px;">
                🚀 How to Sign In
              </h2>
              
              <p style="margin: 0 0 8px 0; font-weight: 600; color: #1e293b;">
                Option 1 — Google Sign-In (Recommended)
              </p>
              <p style="margin: 0 0 16px 0; padding-left: 12px; border-left: 3px solid #1a1f71; font-family: monospace; font-size: 14px; color: #1a1f71; font-weight: bold;">
                {email}
              </p>
              
              <p style="margin: 0 0 8px 0; font-weight: 600; color: #1e293b;">
                Option 2 — Email & Password
              </p>
              <p style="margin: 0 0 24px 0; font-size: 14px; color: #475569;">
                Click <strong>Enroll Now</strong> in the login page, sign up with your authorized email to set up your password, then log in.
              </p>
              
              <!-- CTA Button -->
              <div style="text-align: center; margin: 32px 0;">
                <a href="https://bankpilot.souravmaiti.dev" target="_blank" style="background: #1a1f71; padding: 14px 32px; border-radius: 8px; color: #ffffff; font-weight: bold; text-decoration: none; font-size: 16px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(26, 31, 113, 0.2);">
                  🚀 Launch BankPilot Sandbox
                </a>
              </div>
              
              <!-- Features Container -->
              <div style="background: #f8fafc; border: 1px solid #E5E7EB; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
                <strong style="color: #1a1f71; display: block; margin-bottom: 8px; font-size: 14px;">✨ Explore Key Features:</strong>
                <p style="margin: 0; font-size: 13px; color: #475569; line-height: 1.5;">
                  🤖 AI Assistant &bull; 👤 Customer 360&deg; &bull; 📊 Dynamic Insights &bull; 🔗 Model Context Protocol (MCP) &bull; 🧠 Multi-Agent Architecture
                </p>
              </div>
              
              <!-- Links & Connect Row -->
              <div style="border-top: 1px solid #f1f5f9; padding-top: 20px; text-align: center;">
                <p style="margin: 0 0 16px 0; font-size: 14px; font-weight: 600; color: #1e293b;">
                  Enjoying BankPilot? Let's connect!
                </p>
                <div align="center">
                  <a href="https://github.com/souravmighty/banking-agent" target="_blank" style="display: inline-block; margin: 0 8px; text-decoration: none; color: #1a1f71; font-weight: bold; font-size: 13px;">
                    ⭐ GitHub Code
                  </a>
                  <span style="color: #cbd5e1;">&bull;</span>
                  <a href="https://www.linkedin.com/in/souravmaiti/" target="_blank" style="display: inline-block; margin: 0 8px; text-decoration: none; color: #1a1f71; font-weight: bold; font-size: 13px;">
                    💼 LinkedIn
                  </a>
                  <span style="color: #cbd5e1;">&bull;</span>
                  <a href="https://github.com/souravmighty" target="_blank" style="display: inline-block; margin: 0 8px; text-decoration: none; color: #1a1f71; font-weight: bold; font-size: 13px;">
                    💻 GitHub
                  </a>
                  <span style="color: #cbd5e1;">&bull;</span>
                  <a href="mailto:souravmaiti1997@gmail.com" style="display: inline-block; margin: 0 8px; text-decoration: none; color: #1a1f71; font-weight: bold; font-size: 13px;">
                    📧 Email
                  </a>
                </div>
              </div>
              
            </td>
          </tr>
          
          <!-- Combined Footer -->
          <tr>
            <td style="background: #f8fafc; border-top: 1px solid #E5E7EB; padding: 24px; text-align: center; font-size: 12px; color: #64748b; line-height: 1.5;">
              <p style="margin: 0 0 12px 0;">
                <strong>About BankPilot:</strong> A production-inspired AI banking platform showcasing Generative AI, RAG, and cloud-native Multi-Agent Systems.
              </p>
              <p style="margin: 0 0 12px 0; font-weight: 700; color: #475569;">
                Built with ❤️ by Sourav Maiti
              </p>
              <p style="margin: 0; font-size: 10px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">
                FastAPI &bull; Next.js &bull; Vertex AI &bull; BigQuery &bull; Cloud Run &bull; LangGraph &bull; MCP
              </p>
            </td>
          </tr>
          
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_admin_request_email_html(
    name: str,
    email: str,
    company: str,
    role: str,
    linkedin: str,
    purpose: str,
    requested_at_formatted: str,
    request_id: str
) -> str:
    """
    Generates a premium, theme-maintaining HTML email template for administrative notification of new requests.
    """
    review_url = "https://bankpilot.souravmaiti.dev/staff/demo-requests"
    approve_url = f"https://bankpilot.souravmaiti.dev/staff/demo-requests/{request_id}?action=approve"
    reject_url = f"https://bankpilot.souravmaiti.dev/staff/demo-requests/{request_id}?action=reject"
    
    # Format linkedin display
    linkedin_display = f'<a href="{linkedin}" target="_blank" style="color: #1a1f71; text-decoration: underline; font-weight: 600;">View Profile</a>' if linkedin and linkedin != "N/A" else "N/A"
    
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>New BankPilot Demo Request</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #334155;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f5f7fb; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 720px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.03), 0 4px 6px -4px rgba(0, 0, 0, 0.03); border: 1px solid #E5E7EB;">
          
          <!-- Header Gradient Banner (Admin Control Panel Theme) -->
          <tr>
            <td align="center" style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 40px;">
              <h1 style="margin: 0; color: #ffffff; font-size: 34px; font-weight: 800; letter-spacing: -0.5px;">
                BankPilot
              </h1>
              <p style="margin: 10px 0 0 0; color: #cbd5e1; font-size: 17px; opacity: 0.9;">
                Admin Control Panel
              </p>
            </td>
          </tr>
          
          <!-- Content Body -->
          <tr>
            <td style="padding: 40px; line-height: 1.6; font-size: 15px;">
              <h2 style="color: #1e293b; font-size: 22px; font-weight: 800; letter-spacing: -0.5px; margin: 0 0 8px 0;">New Demo Access Request</h2>
              <p style="margin: 0 0 24px 0; font-size: 14px; color: #64748b;">Submitted: {requested_at_formatted} UTC</p>
              
              <!-- Requester Details Grid -->
              <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; border-radius: 12px; border: 1px solid #E5E7EB; border-collapse: separate; margin-bottom: 32px; overflow: hidden;">
                <tr>
                  <td width="30%" style="padding: 14px 16px; font-size: 12px; font-weight: 700; color: #64748b; border-bottom: 1px solid #E5E7EB; text-transform: uppercase; letter-spacing: 0.5px;">Name</td>
                  <td width="70%" style="padding: 14px 16px; font-size: 14px; font-weight: 700; color: #0f172a; border-bottom: 1px solid #E5E7EB;">{name}</td>
                </tr>
                <tr>
                  <td style="padding: 14px 16px; font-size: 12px; font-weight: 700; color: #64748b; border-bottom: 1px solid #E5E7EB; text-transform: uppercase; letter-spacing: 0.5px;">Email</td>
                  <td style="padding: 14px 16px; font-size: 14px; font-weight: 600; color: #0f172a; border-bottom: 1px solid #E5E7EB; font-family: monospace;">{email}</td>
                </tr>
                <tr>
                  <td style="padding: 14px 16px; font-size: 12px; font-weight: 700; color: #64748b; border-bottom: 1px solid #E5E7EB; text-transform: uppercase; letter-spacing: 0.5px;">Company</td>
                  <td style="padding: 14px 16px; font-size: 14px; color: #334155; border-bottom: 1px solid #E5E7EB;">{company or "N/A"}</td>
                </tr>
                <tr>
                  <td style="padding: 14px 16px; font-size: 12px; font-weight: 700; color: #64748b; border-bottom: 1px solid #E5E7EB; text-transform: uppercase; letter-spacing: 0.5px;">Role</td>
                  <td style="padding: 14px 16px; font-size: 14px; color: #334155; border-bottom: 1px solid #E5E7EB;">{role or "N/A"}</td>
                </tr>
                <tr>
                  <td style="padding: 14px 16px; font-size: 12px; font-weight: 700; color: #64748b; border-bottom: 1px solid #E5E7EB; text-transform: uppercase; letter-spacing: 0.5px;">LinkedIn</td>
                  <td style="padding: 14px 16px; font-size: 14px; border-bottom: 1px solid #E5E7EB;">{linkedin_display}</td>
                </tr>
                <tr>
                  <td style="padding: 16px; font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; vertical-align: top;">Purpose</td>
                  <td style="padding: 16px; font-size: 14px; line-height: 1.5; color: #334155; vertical-align: top;">{purpose or "N/A"}</td>
                </tr>
              </table>
              
              <!-- Quick Admin Action Buttons -->
              <h3 style="margin: 0 0 16px 0; font-size: 13px; font-weight: 800; color: #1e293b; text-transform: uppercase; letter-spacing: 0.5px;">Quick Actions</h3>
              <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td align="center" style="padding-bottom: 20px;">
                    <table border="0" cellpadding="0" cellspacing="0" style="margin: auto;">
                      <tr>
                        <td style="padding: 0 8px;">
                          <a href="{approve_url}" target="_blank" style="background-color: #10b981; color: #ffffff; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 14px; text-decoration: none; display: inline-block; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.15);">
                            Approve Access
                          </a>
                        </td>
                        <td style="padding: 0 8px;">
                          <a href="{reject_url}" target="_blank" style="background-color: #ef4444; color: #ffffff; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 14px; text-decoration: none; display: inline-block; box-shadow: 0 2px 4px rgba(239, 68, 68, 0.15);">
                            Reject Access
                          </a>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td align="center">
                    <a href="{review_url}" target="_blank" style="font-size: 14px; font-weight: 700; color: #1a1f71; text-decoration: none;">
                      Go to Staff Dashboard &rarr;
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="padding: 24px; background-color: #fafbfd; color: #94a3b8; font-size: 11px; text-align: center; border-top: 1px solid #E5E7EB;">
              <p style="margin: 0;">This is an administrative notification dispatched by BankPilot customer-identity-service.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_rejection_email_html(name: str, email: str) -> str:
    """
    Generates a premium, theme-maintaining HTML email template for demo rejection notifications.
    """
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BankPilot Demo Request Update</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #334155;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f5f7fb; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 640px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.03), 0 4px 6px -4px rgba(0, 0, 0, 0.03); border: 1px solid #E5E7EB;">
          
          <!-- Header Gradient Banner (ABC Bank / BankPilot Branding Theme) -->
          <tr>
            <td align="center" style="background: linear-gradient(135deg, #1a1f71 0%, #312e81 100%); padding: 32px;">
              <h1 style="margin: 0; color: #ffffff; font-size: 30px; font-weight: 800; letter-spacing: -0.5px;">
                BankPilot
              </h1>
              <p style="margin: 6px 0 0 0; color: #E3F2FD; font-size: 15px; opacity: 0.9;">
                Production-Inspired AI Banking Platform
              </p>
            </td>
          </tr>
          
          <!-- Content Body -->
          <tr>
            <td style="padding: 32px; line-height: 1.6; font-size: 15px;">
              <h2 style="color: #1e293b; font-size: 20px; font-weight: 800; letter-spacing: -0.5px; margin: 0 0 16px 0; border-bottom: 2px solid #f1f5f9; padding-bottom: 6px;">Demo Request Update</h2>
              <p style="margin: 0 0 16px 0; font-size: 15px; color: #1e293b;">Hi <strong>{name}</strong>,</p>
              <p style="margin: 0 0 16px 0; font-size: 15px; color: #475569;">Thank you for your interest in BankPilot.</p>
              <p style="margin: 0 0 24px 0; font-size: 15px; color: #475569;">Unfortunately, we are unable to approve your sandbox access request at this time.</p>
              <p style="margin: 0 0 24px 0; font-size: 15px; color: #475569;">Thank you for your understanding.</p>
              
              <!-- Links & Connect Row -->
              <div style="border-top: 1px solid #f1f5f9; padding-top: 20px; text-align: center;">
                <p style="margin: 0 0 16px 0; font-size: 14px; font-weight: 600; color: #1e293b;">
                  Want to learn more? Let's connect!
                </p>
                <div align="center">
                  <a href="https://github.com/souravmighty/banking-agent" target="_blank" style="display: inline-block; margin: 0 8px; text-decoration: none; color: #1a1f71; font-weight: bold; font-size: 13px;">
                    ⭐ GitHub Code
                  </a>
                  <span style="color: #cbd5e1;">&bull;</span>
                  <a href="https://www.linkedin.com/in/souravmaiti/" target="_blank" style="display: inline-block; margin: 0 8px; text-decoration: none; color: #1a1f71; font-weight: bold; font-size: 13px;">
                    💼 LinkedIn
                  </a>
                  <span style="color: #cbd5e1;">&bull;</span>
                  <a href="https://github.com/souravmighty" target="_blank" style="display: inline-block; margin: 0 8px; text-decoration: none; color: #1a1f71; font-weight: bold; font-size: 13px;">
                    💻 GitHub
                  </a>
                  <span style="color: #cbd5e1;">&bull;</span>
                  <a href="mailto:souravmaiti1997@gmail.com" style="display: inline-block; margin: 0 8px; text-decoration: none; color: #1a1f71; font-weight: bold; font-size: 13px;">
                    📧 Email
                  </a>
                </div>
              </div>
              
            </td>
          </tr>
          
          <!-- Combined Footer -->
          <tr>
            <td style="background: #f8fafc; border-top: 1px solid #E5E7EB; padding: 24px; text-align: center; font-size: 12px; color: #64748b; line-height: 1.5;">
              <p style="margin: 0 0 12px 0;">
                <strong>About BankPilot:</strong> A production-inspired AI banking platform showcasing Generative AI, RAG, and cloud-native Multi-Agent Systems.
              </p>
              <p style="margin: 0 0 12px 0; font-weight: 700; color: #475569;">
                Built with ❤️ by Sourav Maiti
              </p>
              <p style="margin: 0; font-size: 10px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">
                FastAPI &bull; Next.js &bull; Vertex AI &bull; BigQuery &bull; Cloud Run &bull; LangGraph &bull; MCP
              </p>
            </td>
          </tr>
          
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
