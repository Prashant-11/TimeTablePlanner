# ClassFlow v2.0 License System Testing Guide 🧪

## 🎯 **How to Test the Trial System**

### **Method 1: Using the Testing Tool (Recommended)**

1. **Run the License Testing Tool:**
   ```powershell
   python test_license_system.py
   ```

2. **Test Different Scenarios:**
   - **Fresh Trial (30 days):** Choose option 4
   - **Trial Expiring Soon (7 days):** Choose option 5  
   - **Trial About to Expire (1 day):** Choose option 6
   - **Expired Trial:** Choose option 7
   - **Free Version:** Choose option 8
   - **Premium License:** Choose option 9

3. **After Each Change:**
   - Launch ClassFlow: `python school_timetable_planner_new.py`
   - Observe window title and status bar changes
   - Test clicking on premium features

### **Method 2: Manual License File Editing**

**License File Location:**
- **Windows:** `%APPDATA%\ClassFlow\license.json`
- **Full Path:** `C:\Users\PRASHANT\AppData\Roaming\ClassFlow\license.json`

**To Simulate Expired Trial:**
1. Find the license file
2. Edit `installation_date` to be 35+ days ago
3. Example: Change `"2025-08-10"` to `"2025-07-01"`

---

## ⏱️ **What Happens After 30 Days Trial**

### **Automatic Conversion Process:**

1. **Day 31:** When ClassFlow launches, it detects expired trial
2. **Auto-Conversion:** License automatically changes from `TRIAL` to `FREE`
3. **Feature Restrictions:** Premium features become disabled immediately
4. **UI Updates:** Window title and buttons change to reflect free status

### **License State Changes:**

#### **Before Expiry (Trial Active):**
```json
{
  "license_type": "TRIAL",
  "trial_days": 30,
  "features": {
    "max_classes": 999,
    "max_sections": 999,
    "max_teachers": 999,
    "auto_assign": true,
    "smart_match": true,
    "teacher_restrictions": true,
    "teacher_leave": true,
    "pdf_export": true,
    "watermark": false
  }
}
```

#### **After Expiry (Auto-Converted to Free):**
```json
{
  "license_type": "FREE",
  "trial_days": 0,
  "features": {
    "max_classes": 3,
    "max_sections": 2,
    "max_teachers": 10,
    "auto_assign": false,
    "smart_match": false,
    "teacher_restrictions": false,
    "teacher_leave": false,
    "pdf_export": false,
    "watermark": true
  }
}
```

---

## 🔒 **Features Restricted After Trial**

### **✅ FREE Version - What Still Works:**

| Feature | Status | Details |
|---------|--------|---------|
| **Manual Timetabling** | ✅ Available | Create timetables manually |
| **Basic Editing** | ✅ Available | Add/edit classes, subjects, teachers |
| **Save/Load** | ✅ Available | Auto-save and manual save |
| **Excel Export** | ✅ With Watermark | Exports with "ClassFlow Free" branding |
| **Database Operations** | ✅ Available | All basic CRUD operations |
| **Configuration** | ✅ Limited | Up to 3 classes, 2 sections, 10 teachers |

### **❌ PREMIUM Features - Disabled After Trial:**

| Feature | Status | Restriction Behavior |
|---------|--------|---------------------|
| **Auto-Assign Algorithm** | ❌ Disabled | Button grayed out, shows upgrade dialog |
| **Smart Match** | ❌ Disabled | Button grayed out, shows upgrade dialog |
| **Teacher Restrictions** | ❌ Disabled | Button grayed out, shows upgrade dialog |
| **Teacher Leave Management** | ❌ Disabled | Button grayed out, shows upgrade dialog |
| **PDF Export** | ❌ Disabled | Button grayed out, shows upgrade dialog |
| **Unlimited Scale** | ❌ Limited | Max 3 classes, 2 sections, 10 teachers |

### **📏 Scale Limitations in Free Version:**

```
Classes: Maximum 3 (Class 1, Class 2, Class 3)
Sections: Maximum 2 (A, B)
Teachers: Maximum 10
Periods per Day: Maximum 6
```

---

## 🎭 **UI Changes You'll See**

### **Window Title Changes:**

| License State | Window Title |
|---------------|--------------|
| **30-day Trial** | `ClassFlow v2.0 - Trial: 30 days remaining` |
| **7 days left** | `ClassFlow v2.0 - Trial: 7 days remaining` |
| **1 day left** | `ClassFlow v2.0 - Trial: 1 day remaining` |
| **Expired/Free** | `ClassFlow v2.0 - Free Version` |
| **Premium** | `ClassFlow v2.0 - Premium License` |

### **Status Bar Messages:**

| License State | Status Message |
|---------------|----------------|
| **Trial Active** | 🚀 Trial: X days remaining - Upgrade to Premium for unlimited access! |
| **Trial Expiring** | 🟡 Trial: X days remaining - Upgrade soon to keep advanced features! |
| **Free Version** | 📝 Free Version - Limited features \| Upgrade to Premium for full access |
| **Premium** | ✨ Premium License Active - All features unlocked! |

### **Button States:**

#### **During Trial (All Enabled):**
- ✅ Auto-Assign: Normal blue button
- ✅ Smart Match: Normal blue button  
- ✅ Teacher Restrictions: Normal blue button
- ✅ Teacher Leave: Normal blue button
- ✅ Export PDF: Normal blue button

#### **After Trial (Premium Features Disabled):**
- ❌ Auto-Assign: Grayed out button
- ❌ Smart Match: Grayed out button
- ❌ Teacher Restrictions: Grayed out button  
- ❌ Teacher Leave: Grayed out button
- ❌ Export PDF: Grayed out button
- 🚀 **Upgrade to Premium**: New orange button appears

---

## 🔍 **How to Test Specific Behaviors**

### **Test 1: Fresh Installation**
```powershell
# Delete existing license
python test_license_system.py
# Choose option 10 (Delete license)

# Launch ClassFlow
python school_timetable_planner_new.py
```
**Expected:** New 30-day trial created, all features available

### **Test 2: Trial Expiry Simulation**
```powershell
# Create expired trial
python test_license_system.py
# Choose option 7 (Create expired trial)

# Launch ClassFlow
python school_timetable_planner_new.py
```
**Expected:** Auto-converts to FREE, premium features disabled

### **Test 3: Feature Restriction Testing**
```powershell
# Create free license
python test_license_system.py
# Choose option 8 (Create free license)

# Launch ClassFlow and try clicking:
# - Auto-Assign button → Should show upgrade dialog
# - Teacher Restrictions → Should show upgrade dialog
# - Export PDF → Should show upgrade dialog
```

### **Test 4: Scale Limitation Testing**
1. Create FREE license using testing tool
2. Launch ClassFlow
3. Go to Setup → Configuration
4. Try to add more than 3 classes
5. Try to add more than 2 sections
6. Try to add more than 10 teachers

**Expected:** Should prevent adding beyond limits

### **Test 5: Premium Activation Testing**
```powershell
# Create free license first
python test_license_system.py
# Choose option 8

# Launch ClassFlow
python school_timetable_planner_new.py
# Click "Upgrade to Premium"
# Click "I Have a License Key"
# Enter: CFLOW-SCHOOL-TEST-1234-5678-9012
```
**Expected:** Instant unlock of all features

---

## 📊 **Expected Test Results**

### **Visual Indicators:**

| Test Scenario | Window Title | Status Bar | Button States |
|---------------|--------------|------------|---------------|
| **Fresh Install** | Trial: 30 days | 🚀 Trial: 30 days remaining | All enabled |
| **7 Days Left** | Trial: 7 days | 🟡 Trial: 7 days remaining | All enabled + orange warning |
| **Expired Trial** | Free Version | 📝 Free Version - Limited | Premium disabled |
| **Premium Active** | Premium License | ✨ Premium License Active | All enabled |

### **Feature Behavior:**

| Feature | Trial | Free | Premium |
|---------|-------|------|---------|
| **Click Auto-Assign** | ✅ Works | ❌ Upgrade dialog | ✅ Works |
| **Click Teacher Restrictions** | ✅ Opens dialog | ❌ Upgrade dialog | ✅ Opens dialog |
| **Export PDF** | ✅ Clean export | ❌ Upgrade dialog | ✅ Clean export |
| **Export Excel** | ✅ Clean export | ✅ With watermark | ✅ Clean export |
| **Add 4th Class** | ✅ Allowed | ❌ Prevented | ✅ Allowed |

---

## 🚨 **Important Testing Notes**

### **License File Backup:**
- Always backup your original license before testing
- Use the testing tool's backup option (Option 2)
- Restore when done testing (Option 3)

### **Testing Best Practices:**
1. **Test one scenario at a time**
2. **Close ClassFlow completely between tests**
3. **Check both UI changes and functionality**
4. **Test upgrade dialogs and license activation**
5. **Verify export watermarking behavior**

### **Common Test Issues:**
- **License not updating:** Close and reopen ClassFlow
- **Features still enabled:** Check license file was actually modified
- **Upgrade dialog not showing:** Ensure button is actually disabled

---

## 🎯 **Complete Testing Checklist**

### ✅ **Trial System Tests:**
- [ ] Fresh 30-day trial creation
- [ ] Trial countdown display (window title)
- [ ] Trial countdown display (status bar)
- [ ] 7-day warning messages
- [ ] 1-day final warning
- [ ] Automatic expiry handling

### ✅ **Feature Restriction Tests:**
- [ ] Auto-Assign disabled in FREE
- [ ] Smart Match disabled in FREE
- [ ] Teacher Restrictions disabled in FREE
- [ ] Teacher Leave disabled in FREE
- [ ] PDF Export disabled in FREE
- [ ] Excel export watermarking

### ✅ **Scale Limitation Tests:**
- [ ] 3 classes maximum in FREE
- [ ] 2 sections maximum in FREE
- [ ] 10 teachers maximum in FREE
- [ ] 6 periods maximum in FREE

### ✅ **Premium Activation Tests:**
- [ ] Upgrade dialog appearance
- [ ] License key validation
- [ ] Feature unlock after activation
- [ ] UI updates after activation

### ✅ **User Experience Tests:**
- [ ] Clear upgrade messaging
- [ ] Professional dialog appearance
- [ ] Contact information accuracy
- [ ] Smooth activation flow

---

**🧪 Testing Tool Ready!** Run `python test_license_system.py` to start comprehensive license system testing!
