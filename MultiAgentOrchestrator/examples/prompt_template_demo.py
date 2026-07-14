"""
Prompt Template Management Example - Demonstrates template system with versioning
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from MultiAgentOrchestrator.main import AgentFramework
from MultiAgentOrchestrator.models import AgentConfig, AgentCapabilities, AgentBehavior


async def main():
    """Demonstrate prompt template system with versioning"""
    print("=" * 60)
    print("Prompt Template System Demo")
    print("=" * 60)
    
    # Initialize framework
    print("\n1. Initializing framework...")
    framework = AgentFramework()
    
    # ========================================
    # PART 1: View Default Templates
    # ========================================
    print("\n2. Viewing Default Templates:")
    print("   " + "-" * 50)
    
    default_templates = framework.list_prompt_templates()
    for template in default_templates:
        print(f"\n   Template ID: {template.template_id}")
        print(f"   Name: {template.name}")
        print(f"   Version: {template.version}")
        print(f"   Category: {template.category}")
        print(f"   Usage Count: {template.usage_count}")
        print(f"   Performance Score: {template.performance_score:.2f}")
        print(f"   Variables: {', '.join(template.variables)}")
        print(f"\n   Template Content:")
        print(f"   {template.template[:150]}...")
    
    # ========================================
    # PART 2: Create Custom Template (Version 1.0)
    # ========================================
    print("\n\n3. Creating Custom Template (Version 1.0):")
    print("   " + "-" * 50)
    
    custom_template_v1 = framework.create_prompt_template(
        template_id="sales_assistant_v1",
        name="Sales Assistant v1",
        description="Initial version of sales assistant template",
        template="""You are {agent_name}, a sales representative at {company_name}.

Your role: {agent_description}

Product Information:
{rag_context}

Conversation History:
{history}

Customer Query: {user_input}

Provide a helpful sales response:""",
        variables=["agent_name", "company_name", "agent_description", "rag_context", "history", "user_input"],
        category="sales"
    )
    
    print(f"   ✓ Created: {custom_template_v1.name}")
    print(f"   Version: {custom_template_v1.version}")
    print(f"   Template ID: {custom_template_v1.template_id}")
    
    # ========================================
    # PART 3: Use Template v1 in Agent
    # ========================================
    print("\n4. Creating Agent with Custom Template v1:")
    print("   " + "-" * 50)
    
    config_v1 = AgentConfig(
        agent_name="sales_bot_v1",
        agent_description="Helps customers with product inquiries and sales",
        capabilities=AgentCapabilities(
            prompts=["sales_assistant_v1"],  # Using our custom template
            tools=["calculator"],
            max_iterations=5
        ),
        behavior=AgentBehavior(
            model="llama3.1",
            temperature=0.7,
            max_tokens=512
        )
    )
    
    agent_v1 = await framework.create_and_deploy_agent(config_v1)
    print(f"   ✓ Agent deployed with template v1")
    
    # Test the agent
    print("\n   Testing v1 template...")
    response_v1 = await agent_v1.execute("What products do you have?")
    print(f"   Response: {response_v1[:150]}...")
    
    # Check template usage
    template_after_use = framework.prompt_manager.get_template("sales_assistant_v1")
    print(f"\n   Template Usage Count: {template_after_use.usage_count}")
    
    # ========================================
    # PART 4: Create Improved Template (Version 2.0)
    # ========================================
    print("\n\n5. Creating Improved Template (Version 2.0):")
    print("   " + "-" * 50)
    print("   Improvements: More structured, added tone guidance")
    
    custom_template_v2 = framework.create_prompt_template(
        template_id="sales_assistant_v2",
        name="Sales Assistant v2",
        description="Improved version with better structure and tone guidance",
        template="""You are {agent_name}, a professional sales representative at {company_name}.

ROLE & TONE:
{agent_description}
- Be friendly and consultative
- Focus on customer needs
- Highlight value, not just features

PRODUCT KNOWLEDGE:
{rag_context}

CONVERSATION CONTEXT:
{history}

CUSTOMER INQUIRY:
{user_input}

YOUR RESPONSE (be concise and value-focused):""",
        variables=["agent_name", "company_name", "agent_description", "rag_context", "history", "user_input"],
        category="sales"
    )
    
    # Manually set version to show versioning
    custom_template_v2.version = "2.0.0"
    
    print(f"   ✓ Created: {custom_template_v2.name}")
    print(f"   Version: {custom_template_v2.version}")
    print(f"   Template ID: {custom_template_v2.template_id}")
    
    # ========================================
    # PART 5: Compare Templates Side-by-Side
    # ========================================
    print("\n6. Comparing Template Versions:")
    print("   " + "-" * 50)
    
    v1_template = framework.prompt_manager.get_template("sales_assistant_v1")
    v2_template = framework.prompt_manager.get_template("sales_assistant_v2")
    
    print(f"\n   Version 1.0:")
    print(f"   - Lines: {len(v1_template.template.splitlines())}")
    print(f"   - Length: {len(v1_template.template)} chars")
    print(f"   - Usage: {v1_template.usage_count} times")
    
    print(f"\n   Version 2.0:")
    print(f"   - Lines: {len(v2_template.template.splitlines())}")
    print(f"   - Length: {len(v2_template.template)} chars")
    print(f"   - Usage: {v2_template.usage_count} times")
    print(f"   - Improvements: Better structure, tone guidance, clearer sections")
    
    # ========================================
    # PART 6: Update Existing Template
    # ========================================
    print("\n\n7. Updating Template with New Version:")
    print("   " + "-" * 50)
    
    updated_template = framework.prompt_manager.update_template(
        "sales_assistant_v1",
        {
            "version": "1.1.0",
            "description": "Updated with minor improvements",
            "template": v1_template.template + "\n\n(Be professional and courteous)"
        }
    )
    
    print(f"   ✓ Updated sales_assistant_v1")
    print(f"   New version: {updated_template.version}")
    print(f"   Updated at: {updated_template.updated_at}")
    
    # ========================================
    # PART 7: Template Performance Tracking
    # ========================================
    print("\n8. Template Performance Tracking:")
    print("   " + "-" * 50)
    
    # Simulate performance scores
    print("\n   Simulating template performance scores...")
    
    # Update performance for v1
    for score in [0.75, 0.80, 0.78, 0.82]:
        v1_template.update_performance(score)
    
    # Update performance for v2
    for score in [0.85, 0.88, 0.87, 0.90]:
        v2_template.update_performance(score)
    
    print(f"\n   Template v1.0 Performance: {v1_template.performance_score:.3f}")
    print(f"   Template v2.0 Performance: {v2_template.performance_score:.3f}")
    print(f"   Improvement: +{(v2_template.performance_score - v1_template.performance_score):.3f}")
    
    # ========================================
    # PART 8: List All Templates by Category
    # ========================================
    print("\n\n9. Templates by Category:")
    print("   " + "-" * 50)
    
    categories = {}
    all_templates = framework.list_prompt_templates()
    
    for template in all_templates:
        if template.category not in categories:
            categories[template.category] = []
        categories[template.category].append(template)
    
    for category, templates in categories.items():
        print(f"\n   Category: {category.upper()}")
        for t in templates:
            print(f"   - {t.name} (v{t.version}) - Used {t.usage_count} times, Score: {t.performance_score:.2f}")
    
    # ========================================
    # PART 10: Template Versioning Best Practices
    # ========================================
    print("\n\n10. Template Versioning Best Practices:")
    print("   " + "-" * 50)
    print("""
   Semantic Versioning (MAJOR.MINOR.PATCH):
   
   1.0.0 → 1.0.1  (PATCH)
      - Bug fixes, typo corrections
      - No structural changes
      - Example: Fix grammar in prompt
   
   1.0.0 → 1.1.0  (MINOR)
      - New features, improvements
      - Backward compatible
      - Example: Add new optional variable
   
   1.0.0 → 2.0.0  (MAJOR)
      - Breaking changes
      - Changed structure or variables
      - Example: Complete template redesign
   
   Best Practices:
   ✓ Test new versions before deploying
   ✓ Keep old versions for rollback
   ✓ Track performance metrics
   ✓ Document changes in description
   ✓ Use meaningful template IDs
   """)
    
    # ========================================
    # PART 11: Template Management Methods
    # ========================================
    print("\n11. Available Template Management Methods:")
    print("   " + "-" * 50)
    print("""
   framework.create_prompt_template()    - Create new template
   framework.list_prompt_templates()     - List all templates
   framework.prompt_manager.get_template()        - Get specific template
   framework.prompt_manager.update_template()     - Update existing template
   framework.prompt_manager.delete_template()     - Delete template
   framework.prompt_manager.get_template_performance()  - Get metrics
   
   Template Object Methods:
   template.render(context)              - Render with variables
   template.increment_usage()            - Track usage
   template.update_performance(score)    - Update metrics
   """)
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "=" * 60)
    print("Template System Demo Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("✓ Templates are centrally managed")
    print("✓ Support versioning and performance tracking")
    print("✓ Easy to create, update, and compare versions")
    print("✓ Automatic usage counting and metrics")
    print("✓ Can be organized by category")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
