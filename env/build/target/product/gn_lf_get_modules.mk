GN_MODULES_TEMP := $(shell find $(TRANSAGE_BUILD_CODE_DIR) -name "Android.mk" 2>/dev/null | xargs sed  -ne  "/^\<LOCAL_PACKAGE_NAME\>/p" -ne "/^\<LOCAL_MODULE\>/p")
GN_MODULES := $(filter-out LOCAL_MODULE LOCAL_PACKAGE_NAME :=,$(GN_MODULES_TEMP))

ifneq ($(GN_MODULES),)
   PRODUCT_PACKAGES += $(GN_MODULES)
endif

$(foreach p, $(PRODUCT_PACKAGES), $(info building $(p)))
#$(error $(PRODUCT_PACKAGES))
